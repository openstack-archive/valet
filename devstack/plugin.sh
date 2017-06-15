#!/usr/bin/env bash
# plugin.sh - DevStack plugin.sh dispatch script template

# check for service enabled
if is_service_enabled valet; then
    CWD=`pwd`

    if [ -z ${HOST_IP} ]; then
        echo "HOST_IP is not set.  It must be set to install/configure Valet!"
        return 1
    fi
    if [ -z ${HOME} ]; then
        echo "HOME is not set.  It must be set to install/configure Valet!"
        return 1
    fi

    echo "HOME = ${HOME}"
    echo "HOST_IP = ${HOST_IP}"

    cd ${HOME}

    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then

        # set hostname to standard region/rack/node format
        # so that the topology will be understood properly
        # by Valet. Put that hostname, and valet into /etc/hosts.
        sudo hostname Region1r001c001
        if [[ ! `grep "Region1r001c001" /etc/hosts` ]]; then
            CMD='echo "${HOST_IP}   Region1r001c001 valet" >> /etc/hosts'
            sudo bash -c ${CMD}
        fi
    fi

    if [[ "$1" == "stack" && "$2" == "extra" ]]; then
        if [ ! -d ${HOME}/.valet_venv ]; then
            echo "Creating new virtual environment for Valet..."
            virtualenv .valet_venv
        fi
        source .valet_venv/bin/activate
        
        export HOST_IP=${HOST_IP}
        /opt/stack/valet/devstack/stack-valet-music-install.sh
        sudo -E bash -c /opt/stack/valet/devstack/stack-valet-music-configure.sh
        /opt/stack/valet/devstack/stack-valet-python-install.sh
        /opt/stack/valet/devstack/stack-valet-valet-install.sh
        sudo -E bash -c /opt/stack/valet/devstack/stack-valet-valet-configure.sh
        /opt/stack/valet/devstack/stack-valet-services-start.sh
        /opt/stack/valet/devstack/stack-valet-openstack-configure.sh

        # Then the user needs to run the manual steps laid out in 
        # the following file;
        #   stack-valet-plugins-configure-manual.sh
        deactivate
    fi

    if [[ "$1" == "unstack" ]]; then
        source .valet_venv/bin/activate

        /opt/stack/valet/devstack/unstack-valet-services-stop.sh
        deactivate
    fi

    if [[ "$1" == "clean" ]]; then
        source .valet_venv/bin/activate

        sudo bash -c /opt/stack/valet/devstack/clean-valet-uninstall.sh
        /opt/stack/valet/devstack/clean-valet-cleanup.sh
        deactivate
        rm -rf ${HOME}/.valet_venv
    fi
    cd ${CWD}
fi
