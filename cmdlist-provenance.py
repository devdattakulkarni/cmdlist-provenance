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


def cleanup(program_name):
    dir_path = "/tmp/{program_name}"
    dir_path = dir_path.format(program_name=program_name)
    shutil.rmtree(dir_path)


def copy_verification_file(dir_path, verification_script_path):
    verification_file_name = verification_script_path
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
    current_dir = os.getcwd()
    os.chdir(dir_path)

    image_name = program_name

    #docker build -t image_name .
    docker_build_cmd = "docker build -t {image_name} ."
    docker_build_cmd = docker_build_cmd.format(image_name=image_name)

    docker_build_success = False
    try:
        docker_build_output = subprocess.check_output(docker_build_cmd,
                                                      shell=True)
        print "Docker build output:%s" % docker_build_output
        docker_build_success = True
    except subprocess.CalledProcessError as e:
        print "Docker build error: %s" % e

    if not docker_build_success:
        return docker_build_success

    #docker run image_name
    docker_run_cmd = "docker run {image_name}"
    docker_run_cmd = docker_run_cmd.format(image_name=image_name)

    docker_run_success = False
    try:
        docker_run_output = subprocess.check_output(docker_run_cmd, shell=True)
        print "Docker run output:%s" % docker_run_output
        docker_run_success = True
    except subprocess.CalledProcessError as e:
        print "Docker run error: %s" % e
    
    os.chdir(current_dir)

    return docker_build_success and docker_run_success 


def check_if_cmd_list_provenance(program_name, cmdlist, dir_path, verification_file_name):
    # Generate dockerfile from the cmdlist
    # Inject the verification script in the Dockerfile
    # Build the docker container
    # Run the docker container
    # Check the output of the run docker container command
    
    create_docker_file(dir_path, cmdlist, verification_file_name)

    docker_run_status = docker_build_and_run(dir_path, program_name)

    return docker_run_status


def find_provenance(program_name, cmdfile, verification_script_path):
    navigation_cmds = ['cd', 'pushd', 'popd']
    listing_cmds = ['ls', 'history', 'ps']
    viewing_cmds = ['less', 'more', 'man']
    editing_cmds = ['emacs', 'vi']
    #remote_io_cmds = ['git']

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

                # Even if the command passes all the above filters,
                # it may fail within docker build because the layer
                # that we are dealing with may not have that command
                # installed on it.
                # A command, such as curl may work on the host because
                # it is already installed on it. If we just copy that to the candidate_list then
                # there is a possibility that the docker build will fail. Our main goal is to
                # not let the docker build fail.
                # So a strategy we follow is to find out if 'l' is installed on the host.
                # We can do this using the following command:
                # dpkg --get-selections | grep -v deinstall | grep tomcat8
                # If the output is non-empty then we know that host has this package installed.
                # We add that package to the list of packages to be installed prior to trying
                # the candidate_list.
                # Output of the above command might be non-empty but still executing that command
                # may not be correct -- it may not be a command but a service. If this command
                # gets added to the Dockerfile then the docker build will fail. One approach to
                # address this issue is to run the command on host and check if the output contains
                # a well-known string, such as "command not found:". If so, we don't include the
                # command in the candidate_list.
                # How do we deal with file modifications? Would copying the modified file into the
                # container at the appropriate location be enough?
                # How do you break up a command such as curl -sSL https://get.docker.com/ubuntu/ | sudo sh
                # into two? This may be required as we have observed that such piped combined commands
                # don't seem to work as part of docker's RUN command
                # One option is to break the command at pipe based redirection to save the output in a file
                # and then use 'sh' to execute that file.
                # Certain commands may need one or more flags to be tried on the command line. How do we find
                # out which flags to use?
                # Most probably in the vicinity of the command there are similar commands with different flags
                # We need to find out one of those commands which is really going to work. We could maintain
                # a similar_command_map which maintains a map of <command, [similar cmd list]> similar commands.
                # We try each command as part of the 'docker build' and keep the one which works.

                # Note that we cannot ignore 'git clone' commands as these commands are typically used to download
                # the required software/package.
                # Also, cd/pushd/popd commands need to be combined with their immediate successor commands to be
                # included as part of a single Docker RUN command. Otherwise they won't take effect.

                # What do we do about environment variable setting commands, such as export or variable assignment?
                # We can set these using ENV command in Dockerfile. 

                # What about variable assignments (such as: pip_command=`which pip`)?
                
                # What about file copy commands (such as:
                # cp /opt/docker-registry/docker_registry/lib/../../config/config_sample.yml /opt/docker-registry/docker_registry/lib/../../config/config.yml

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

    #cleanup(program_name)
    print "done."

    
if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 4:
        print "python cmdlist-provenance <program-name> <cmdlist> <path-to-verification-script>"
        exit(0)

    program_name = sys.argv[1]
    cmdfile = sys.argv[2]
    verification_script_path = sys.argv[3]

    find_provenance(program_name, cmdfile, verification_script_path)
