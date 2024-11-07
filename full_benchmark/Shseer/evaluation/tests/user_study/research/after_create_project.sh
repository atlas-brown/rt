#!/bin/bash

project_dir=$1
virtual_env=$2
python_version=$3

VIRTUALENV_PATTERN="^([a-zA-Z0-9.-]+)..created.+versions.(.+).$"
VERSION_PATTERN="^[a-zA-Z0-9.-]+$|^[a-zA-Z0-9.-]+\s"

is_available_python_version=false
is_available_virtualenv=false

separator() { printf %$1s | tr " " "-" && echo ""; }

echo_message() { separator $2 && echo -e $1 && separator $2; }

cd ../

if [[ $project_dir == "" ]]; then
	echo_message "You did not specify project dir, virtual env and python version." 64
else
	if [[ -d $project_dir ]]; then
		echo_message "Directory '"$project_dir"' exists.\
			\nRemove directory '"$project_dir"'?\
			\nPress 'Enter' or 'y' to delete or any key to exit." 50

		read -s -n 1 delete

		if [[ $delete == "" || $delete == "y" ]]; then
			rm -rf $project_dir
			echo "Directory removed."
		else
			echo "Exit" && exit 1
		fi
	fi
fi

if [[ $virtual_env != "" ]]; then

	while read -r line; do
		if [[ $line =~ ${VIRTUALENV_PATTERN} ]]; then
			pyenv_version=${BASH_REMATCH[2]}
			if [[ $virtual_env =~ ${BASH_REMATCH[1]} ]]; then
				is_available_virtualenv=true
				echo_message "Virtualenv '"$virtual_env"' already exists \
					('"$pyenv_version"').\nSet virtualenv '"$virtual_env"' for \
					project dir with '"$pyenv_version"'?\nPress 'Enter' or 'y' \
					to continue or any key to exit." 60
			fi
		fi
	done < <(pyenv virtualenvs)

	if $is_available_virtualenv; then
		read -s -n 1 answer

		if [[ $answer == "" || $answer == "y" ]]; then
			mkdir $project_dir && cd $project_dir
			pyenv local $virtual_env
		else
			rm -rf $project_dir
			echo "Exit" && exit 1
		fi
	fi

	if [[ $python_version != "" ]]; then
		while read -r line; do
			if [[ $line =~ ${VERSION_PATTERN} ]]; then
				if [[ $python_version =~ ${BASH_REMATCH[1]} ]]; then
					is_available_python_version=true
				fi
			fi
		done < <(pyenv versions)

		if ! $is_available_python_version; then
			{
				pyenv install $python_version
			} || {
				echo "" && echo "Exit"
				rm -rf $project_dir && exit 1
			}

			is_available_python_version=true
		fi
	else
		if ! $is_available_virtualenv; then
			echo_message "There are no available virtualenvs.\nYou must \
				specify the version of Python." 65
			exit 1
		fi
	fi

	if $is_available_python_version && ! $is_available_virtualenv; then
		pyenv virtualenv $python_version $virtual_env
		mkdir $project_dir && cd $project_dir
		pyenv local $virtual_env
		echo "" && echo "Done"
	fi
else
	echo_message "You did not specify virtual env and python version." 51
fi

django_project_name="${project_dir//'-'/$'_'}"

pip install --upgrade pip

{
	pip freeze | grep Django
} || {
	pip install django
}

django-admin startproject $django_project_name

mv $django_project_name/manage.py ./
mv $django_project_name/$django_project_name/* $django_project_name
rm -rf $django_project_name/$django_project_name/

python manage.py migrate
python manage.py createsuperuser
