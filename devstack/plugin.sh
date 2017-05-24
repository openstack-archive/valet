# plugin.sh - DevStack plugin.sh dispatch script template

# check for service enabled
if is_service_enabled valet; then

     if [[ "$1" == "stack" && "$2" == "install" ]]; then
         # Perform installation of service source
         echo_summary "Installing Valet"
         # Calls function defined in devstack/lib/databases/mysql
         recreate_database valet
         python $DEST/valet/valet/db/api.py build-db
    fi

    if [[ "$1" == "clean" ]]; then
        rm -rf $DEST/valet
    fi
fi
