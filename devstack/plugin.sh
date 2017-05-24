# plugin.sh - DevStack plugin.sh dispatch script template

# check for service enabled
if is_service_enabled valet; then

     if [[ "$1" == "stack" && "$2" == "install" ]]; then
         # Perform installation of service source
         echo_summary "Installing Valet"
         recreate_database valet
    fi
fi

