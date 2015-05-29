#!/bin/python

# Author: Devdatta Kulkarni (devdatta@cs.utexas.edu)

import os
import re
import shutil
import subprocess
import sys


def is_filtered_command(cmd, cmdlist):
    for c in cmdlist:
        pattern = c
        reg = re.compile(pattern)
        m = reg.match(cmd)
        if m is not None:
            return True
    return False


def create_dir(program_name):
    dir_path = "/tmp/{program_name}"
    dir_path = dir_path.format(program_name=program_name)
    os.mkdir(dir_path, 555)
    print "Dir path:%s" % dir_path
    return dir_path


def copy_verification_file(dir_path, verification_script_path):
    verification_file_name = ''
    shutil.copy(verification_script_path, dir_path)
    k = verification_script_path.rfind("/")
    if k >= 0:
        verification_file_name = verification_script_path[k+1:]
    print "Verification file name: %s" % verification_file_name
    return verification_file_name


def create_docker_file(dir_path, cmdlist, verification_file_name):
    file_path = dir_path + "/Dockerfile"
    fw = open(file_path, "w")

    fw.write("FROM ubuntu:precise\n")

    for c in reversed(cmdlist):
        fw.write("RUN " + c + "\n")

    fw.write("COPY " + verification_file_name + " /root/" + verification_file_name + "\n")
    
    entry_point = "ENTRYPOINT [\"bash\", \"/root/" + verification_file_name + "\"]"
    print "Entry point:%s" % entry_point
    fw.write(entry_point)
    fw.close()


def docker_build_and_run(dir_path, program_name):
    docker_build_run_success = False

    current_dir = os.getcwd()
    print "Current dir:%s" % current_dir

    os.chdir(dir_path)
    new_current_dir = os.getcwd()
    print "New current dir:%s" % new_current_dir    

    image_name = program_name

    #docker build -t image_name .
    docker_build_cmd = "docker build -t {image_name} ."
    docker_build_cmd = docker_build_cmd.format(image_name=image_name)

    try:
        docker_build_output = subprocess.check_output(docker_build_cmd,
                                                      shell=True)
        print "Docker build output:%s" % docker_build_output
    except subprocess.CalledProcessError as e:
        print(e)

    #docker run image_name
    docker_run_cmd = "docker run {image_name}"
    docker_run_cmd = docker_run_cmd.format(image_name=image_name)

    try:
        docker_run_output = subprocess.check_output(docker_run_cmd, shell=True)
        print "Docker run output:%s" % docker_run_output
        docker_build_run_success = True
    except subprocess.CalledProcessError as e:
        print(e)
    
    os.chdir(current_dir)

    return docker_build_run_success


def check_if_cmd_list_provenance(program_name, cmdlist, dir_path, verification_file_name):
    # Generate dockerfile from the cmdlist
    # Inject the verification script in the Dockerfile
    # Build the docker container
    # Run the docker container
    # Check the output of the run docker container command
    
    create_docker_file(dir_path, cmdlist, verification_file_name)

    docker_run_status = docker_build_and_run(dir_path, program_name)

    return docker_run_status


if len(sys.argv) < 4 or len(sys.argv) > 4:
    print "python cmdlist-provenance <program-name> <cmdlist> <path-to-verification-script>"
    exit(0)

program_name = sys.argv[1]
cmdfile = sys.argv[2]
verification_script_path = sys.argv[3]


navigation_cmds = ['cd', 'pushd', 'popd']
listing_cmds = ['ls', 'history']
viewing_cmds = ['less', 'more']
editing_cmds = ['emacs', 'vi']

anchor_cmds = ['apt-get update']

f = open(cmdfile, 'r')

lines_in_file = []

pattern = '^\d+ '
reg = re.compile(pattern)

for line in f:
    line = line.strip()
    m = reg.match(line)
    if m is not None:
        line = line.replace(m.group(0), '')
        lines_in_file.append(line.strip())

print "Lines in file:"
print lines_in_file

dir_path = create_dir(program_name)
verification_file_name = copy_verification_file(dir_path, verification_script_path)

candidate_list = []

provenance_generated = False
end_of_cmds = False
while not provenance_generated and not end_of_cmds:

    for l in reversed(lines_in_file):
        if (not is_filtered_command(l, navigation_cmds) and
            not is_filtered_command(l, listing_cmds) and
            not is_filtered_command(l, viewing_cmds) and
            not is_filtered_command(l, editing_cmds)):
            candidate_list.append(l)

        if is_filtered_command(l, anchor_cmds):
           print "Candidate list:"
           print candidate_list

           provenance_generated = check_if_cmd_list_provenance(program_name,
                                                               candidate_list,
                                                               dir_path,
                                                               verification_file_name)
           if provenance_generated:
                print "Provenance found for %s" % program_name
                print "Command list:"
                for c in reversed(candidate_list):
                    print c
                break
    end_of_cmds = True

print "done."
    
#for l in reversed(lines_in_file):
#    if l not in listing_cmds:
#        print l
#    if not check_if_exists(l, listing_cmds):
#        print l
#exit(0)
