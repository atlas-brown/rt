#!/bin/bash

function restore_db(){
    docker run --name=${package_name}_db --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_USER=www-data --env=POSTGRES_DB=gmf_${package_name} --env=PGPASSWORD=www-data --env=PGUSER=www-data --env=PGDATABASE=gmf_$package_name --detach --publish=65432:5432 camptocamp/postgres:10
    # simply wait for the DB to be ready
    until docker exec ${package_name}_db psql -c "SELECT schema_name FROM information_schema.schemata;" 2> /dev/null ; do
        echo "waiting for the DB to be up"
        sleep 1
    done
    echo "importing database"
    myTest=$(docker exec ${package_name}_db psql -tc "SELECT count(*) from ne_10m_lakes")
    if [[ ! ${myTest} -gt 1 ]] ; then
      docker exec -i ${package_name}_db pg_restore -d gmf_${package_name} < sample/sample_db.dump
    fi
    echo "migrate DB schemas"
    docker-compose exec geoportal alembic --config=alembic.ini --name=main upgrade head
    docker-compose exec geoportal alembic --config=alembic.ini --name=static upgrade head
}

function create_db(){
    # start and initialize DB
    docker run --name=${package_name}_db --env=POSTGRES_PASSWORD=www-data --env=POSTGRES_USER=www-data --env=POSTGRES_DB=gmf_${package_name} --env=PGPASSWORD=www-data --env=PGUSER=www-data --env=PGDATABASE=gmf_$package_name --detach --publish=65432:5432 camptocamp/postgres:10
    until docker exec ${package_name}_db psql -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2> /dev/null ; do
        echo "waiting until DB is ready to accept connections"
    	sleep 1;
    done
    # create extensions
    docker exec ${package_name}_db psql -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
    docker exec ${package_name}_db psql -c "CREATE EXTENSION IF NOT EXISTS hstore;"
    docker exec ${package_name}_db psql -c "CREATE SCHEMA main;"
    docker exec ${package_name}_db psql -c "CREATE SCHEMA main_static;"
    # migrate DB schemas
    docker-compose exec geoportal alembic --config=alembic.ini --name=main upgrade head
    docker-compose exec geoportal alembic --config=alembic.ini --name=static upgrade head
    # add sample data
    # try if already existing
    docker exec package_gmf_db psql -c "SELECT COUNT(*) FROM ne_10m_ocean;" 2> /dev/null
    # if not import sample data from geopackage
    if [[ ! $? -eq  0 ]] ; then
        echo "importing sample data"
        ogr2ogr -nlt PROMOTE_TO_MULTI  -f "PostgreSQL" PG:"host=localhost port=65432 user=www-data dbname=gmf_${package_name} password=www-data" sample/package_gmf.gpkg
        # FIXME: should fix the problem where geoportal cannot update the table instead of hacking it like this:
        docker exec package_gmf_db psql -c "UPDATE main_static."user" SET is_password_changed = true WHERE username ilike 'admin';"
    fi
}

function run(){
    cp docker-compose.override.{sample.,}yaml
    ./build
    docker-compose up -d
}

function configure_full_text_search(){
    echo 'Configure full text search'
    docker exec ${package_name}_db psql -c "CREATE EXTENSION IF NOT EXISTS unaccent;"

    # Configure full text search
    docker exec ${package_name}_db psql -c "CREATE TEXT SEARCH CONFIGURATION en (COPY = english);"
    docker exec ${package_name}_db psql -c "ALTER TEXT SEARCH CONFIGURATION en ALTER MAPPING FOR hword, hword_part, word WITH unaccent, english_stem;"
    docker exec ${package_name}_db psql -c "CREATE TEXT SEARCH CONFIGURATION de (COPY = german);"
    docker exec ${package_name}_db psql -c "ALTER TEXT SEARCH CONFIGURATION de ALTER MAPPING FOR hword, hword_part, word WITH unaccent, german_stem;"
    # Set CRS for tsearch to 3857
    docker exec ${package_name}_db psql -c "SELECT UpdateGeometrySRID('main', 'tsearch', 'the_geom', 3857);"
}

function create_tsearch_table(){
    tsearchTableTest=$(docker exec ${package_name}_db psql -tc "SELECT count(*) from main.tsearch")
    if [[ ! ${tsearchTableTest} -gt 1 ]] ; then
        echo 'Create tsearch table'
        docker exec ${package_name}_db psql -c "
        INSERT INTO main.tsearch (the_geom, layer_name, label, public, role_id, lang, ts)
        SELECT
            ST_TRANSFORM(wkb_geometry, 3857),
            'Country',
            name,
            't',
            NULL,
            NULL,
            to_tsvector('en', name) || to_tsvector('de', name)
        FROM ne_10m_admin_0_sovereignty;
        "
        docker exec ${package_name}_db psql -c "
        INSERT INTO main.tsearch (the_geom, layer_name, label, public, role_id, lang, ts)
        SELECT
            ST_TRANSFORM(geom, 3857),
            'Place',
            name,
            't',
            NULL,
            NULL,
            to_tsvector('en', name) || to_tsvector('de', name)
        FROM karlsruhe_place;
        "
    fi
}

# MAIN
function main(){
    run
#    create_db
    restore_db
    # configure_full_text_search
    create_tsearch_table
    docker-compose down
    docker-compose up -d
}

package_name=${1:-"package_gmf"}
db_storage=${2:-"/tmp/postgres-data"}
# if file is executed and not sourced
if [[ "${BASH_SOURCE[0]}" = "${0}" ]] ; then
    main
fi

