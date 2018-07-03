# CLARTIY DOCKER CKAN

See [Installing CKAN with Docker Compose](http://docs.ckan.org/en/2.8/maintaining/installing/install-from-docker-compose.html)

You can set default values for any environment variables referenced in the Compose file, or used to configure Compose, in an [environment file named .env](https://docs.docker.com/compose/environment-variables/#set-environment-variables-with-docker-compose-run).
Copy contrib/docker/.env.template to contrib/docker/.env and follow instructions within to set passwords and other sensitive or user-defined variables. 

*Note*: contrib/docker/.env added to .gitignore!

### Backup / Restore:

- ``/home/pascal/git_work/docker-ckan/contrib/docker/.env``
- named volumes: ``/var/lib/docker/volumes/docker_ckan_*``