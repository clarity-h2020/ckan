# CLARITY CKAN

## Description

### CKAN: The Open Source Data Portal Software

**[CKAN](http://ckan.org/) is the world’s leading open-source data portal platform**.
CKAN makes it easy to publish, share and work with data. It's a data management
system that provides a powerful platform for cataloging, storing and accessing
datasets with a rich front-end, full API (for both data and catalog), visualization
tools and more.

### ckan.myclimateservice.eu

CLARITY's online meta-data catalogue available at [ckan.myclimateservice.eu](https://ckan.myclimateservice.eu/) reports on all datasets produced and used within the [CLARITY H2020 project](https://clarity-h2020.eu/). It has been used as a “living” **Data Management Plan** during the course of the project. Datasets therein are described by meta-data compliant to the [DataCite](https://datacite.org/)  metadata schema with CLARITY-specific extensions. The actual data is not stored in the meta-data catalogue directly but in the repositories of the original data provider (data used) and in private (non-open data produced) or public (open data produced) repositories selected or maintained by CLARITY partners. Thereby, the default repository for depositing open data produced by CLARITY is the [Zenodo](https://zenodo.org/communities/clarity) research data repository. The meta-data in the catalogue contains either the public URL for accessing the dataset and/or the contact details of the responsible data provider for requesting access to (non-public) data.

## Implementation 

CLARTIY CKAN is based on the [official CKAN](https://github.com/ckan/ckan) repository and has among others been cloned to implement some changes to the [docker compose file](https://github.com/clarity-h2020/ckan/blob/csis-dev.ait.ac.at/contrib/docker/docker-compose.yml).

### Data Management Plan

CLARITY team has implemented a fully automatic procedure to generate [offline documents](https://github.com/clarity-h2020/data-management-plan/releases) out of the online catalogue. The respective source code is hosted on GitHub in repository [clarity-h2020/data-management-plan](https://github.com/clarity-h2020/data-management-plan/) and can be executed automatically when changes to the online catalogue have been made. 

## Deployment

CLARTIY CKAN is deployed as a set of docker containers on [CSIS Development System](https://github.com/clarity-h2020/csis#csis-development-system) virtual server. A separate [nginx-proxy](https://github.com/clarity-h2020/docker-compose-letsencrypt-nginx-proxy-companion/tree/csis-dev.ait.ac.at) exposed the internal CKAN service to ckan.myclimateservice.eu. 

### Building the Docker Image

Building the docker image is straightforward:

```sh
cd /docker/500-ckan
docker-compose build
```

### Configuring and starting the containers
Containers are managed via the customised [docker-compose.yml](https://github.com/clarity-h2020/ckan/blob/csis-dev.ait.ac.at/contrib/docker/docker-compose.yml). The actual configuration is maintained in an `.env` while [.env.template](https://github.com/clarity-h2020/ckan/blob/csis-dev.ait.ac.at/contrib/docker/.env.template) can be used as blueprint of this configuration file. Variables in this file will be substituted into docker-compose.yml.

The CKAN containers can be started with

```sh
cd /docker/500-ckan
docker-compose up -d --force-recreate --remove-orphans
```

After that, the search index of the Redis container should be [rebuilt](https://github.com/clarity-h2020/ckan/issues/11):

```sh
docker exec -t ckan-ckan bash -c \
'source /usr/lib/ckan/venv/bin/activate \
&& cd /usr/lib/ckan/venv/src/ckan \
&& ckan-paster search-index rebuild \
--config "${CKAN_CONFIG}"/production.ini'
```
### Data Volumes

Data of different containers is stored in the following **named volues**:

- 'ckan_config' in `/var/lib/docker/volumes/ckan_config`
- 'ckan_home' in `/var/lib/docker/volumes/ckan_home`
- 'ckan_storage' in `/var/lib/docker/volumes/ckan_storage`
- 'ckan_pg-data' in `/var/lib/docker/volumes/ckan_pg-data`

### Upgrading CKAN

For upgrading CKAN it is necessary to rebase the [csis-dev.ait.ac.at](https://github.com/clarity-h2020/ckan/tree/csis-dev.ait.ac.at) branch onto [ckan:master](https://github.com/ckan/ckan/compare/master...clarity-h2020:csis-dev.ait.ac.at). Alternatively, the updated [ckan Docker image](https://hub.docker.com/r/ckan/ckan) can be referenced in [docker+compose](https://github.com/clarity-h2020/ckan/blob/csis-dev.ait.ac.at/contrib/docker/docker-compose.yml).

Before upgrading it is advisable to perform an incremental backup:

```sh
cd /docker/999-duplicity/
docker-compose up
```

Data Volumes as well as the `/docker/500-ckan` directory are are included in [/docker-duplicity](https://github.com/clarity-h2020/docker-duplicity/tree/csis-dev.ait.ac.at) backups configuration.

## Copying and License

This material is copyright (c) 2006-2018 Open Knowledge Foundation and contributors.

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0
whose full text may be found at:

http://www.fsf.org/licensing/licenses/agpl-3.0.html
