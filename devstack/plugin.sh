if is_service_enabled valet; then
    

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        if [[ ${valet_db_engine} == "mysql" ]]; then
         recreate_database valet
        fi
        if [[ ${valet_db_engine} == "mysql" ]]; then
         python $DEST/valet/valet/db/api.py build-db
        fi
    fi

    if [[ "$1" == "clean" ]]; then
        rm -rf $DEST/valet
    fi
fi
