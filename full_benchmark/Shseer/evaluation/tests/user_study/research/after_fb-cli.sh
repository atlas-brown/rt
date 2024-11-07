#!/bin/bash

# load helper functions
source $fbrd/fb_cli/utils.sh

# check that all dependencies are installed for running the local minikube cluster
function checkThatLocalDevDependenciesAreInstalled {
  [ ! -x "$(command -v minikube)" ] && echo "Please install minikube ..." && exit
  [ ! -x "$(command -v arkade)" ]   && echo "Please install arkade ..."   && exit
  [ ! -x "$(command -v faas-cli)" ] && echo "Please install faas-cli ..." && exit
  [ ! -x "$(command -v kubectl)" ]  && echo "Please install kubectl ..."  && exit
}

# create a local development environment using openfaas on minikube
function bootstrapOpenfaasLocally {
  checkThatLocalDevDependenciesAreInstalled
  bash "$fbrd/fb_cli/bootstrap_openfaas_locally.sh"
}

# destroy the created development environment
function teardownOpenfaasLocally {
  checkThatLocalDevDependenciesAreInstalled
  bash "$fbrd/fb_cli/teardown_openfaas_locally.sh"
}

function startMinikube {
  mkstatus=$(minikube status)
  if [[ $mkstatus =~ "There is no local cluster" ]] ; then
    pmsg "Openfaas has not been bootstrapped, creating now..."
    bootstrapOpenfaasLocally
  elif [[ $mkstatus =~ "host: Running" ]] ; then
    errmsg "Minikube is already running, will do nothing ..."
  elif [[ $mkstatus =~ "host: Stopped" ]] ; then
    pmsg "Starting minikube ..."
    minikube start
    pmsg "Starting port forward ..."
    kubectl port-forward -n openfaas svc/gateway 8080:8080 &
    echo
    smsg "OpenFaas on minikube ready for running experiments locally."
  fi
}

function fixMinikubePortForward {
  msg "Attempting to start port forwarding again ..."
  kubectl port-forward -n openfaas svc/gateway 8080:8080 &
  echo
}

function stopMinikube {
  pmsg "Stopping minikube ..."
  minikube stop
  pmsg "Stopping any lingering kubectl processes ..."
  killall -q kubectl
  smsg "Done stopping minikube."
}

function checkValidExperimentName {
  # get existing experiment names
  experiment_names=$(ls experiments)
  # check that name is unique
  echo "$experiment_names" | grep -qw "$1" && return 1
  # check that name is valid
  [[ "$1" =~ ^[a-zA-Z-]*$ ]] || return 1
  # return true if both checks are good
  return 0
}

function checkThatExperimentExists {
  # get existing experiment names
  experiment_names=$(ls experiments)
  # check that experiment exists
  echo "$experiment_names" | grep -qw "$1" && return 0
  errmsg "Invalid experiment name."
  return 1
}

function firstTimeInfrastrutureBootstrap {
  bash "$fbrd/fb_cli/first_time_infrasctructure_bootstrap.sh"
}

function destroyPermanentInfrastructure {
  bash "$fbrd/fb_cli/destroy_permanent_infrastructure.sh"
}

function sshOrchestrator {
  cd "$fbrd/infrastructure/orchestrator"
  ssh ubuntu@$TF_VAR_orchstrator_static_ip -i "$fbrd/secrets/ssh_keys/orchestrator"
  cd "$fbrd"
}

function sshDBServer {
  cd "$fbrd/infrastructure/db_server"
  ssh ubuntu@$TF_VAR_db_server_static_ip -i "$fbrd/secrets/ssh_keys/db_server"
  cd "$fbrd"
}

# create files for a new experiment from templates
function createExperiment {
  read -rp "New experiment name [a-zA-Z-]: " exp_name
  checkValidExperimentName "$exp_name" \
    && bash "$fbrd/fb_cli/create_experiment.sh" "$exp_name" \
    || ( errmsg "Invalid Experiment name ... aborting" && exit )
}

function listExperiments {
  ls -I "*.md" "$fbrd/experiments"
}

function updateExperimentInfraTemplates {
  msg "This will update the templates in each faas-benchmarker/experiments/<experiment> directory"
  msg "With the templates in faas-benchmarker/infrastructure/templates/"
  msg "would you like to proceed? [yes/no]"
  read -n 3 -r ; echo
  if [[ $REPLY =~ ^yes$ ]]; then
    for exp in $(listExperiments) ; do
      stmsg "Updating infrastructure templates for experiment: $exp"
      bash "$fbrd/fb_cli/copy_infrastructure_templates_to_experiment.sh" "$exp"
      smsg "Finished updating infrastructure templates for experiment: $exp"
    done
  else
    errmsg "Cancelling."
  fi
}

function chooseExperiment {
  experiments=$(listExperiments)
  experiments+=" cancel"
  select exp in $experiments ; do
    case "$exp" in
      # allow to go cancel
      cancel)
        echo ""
        break 1
        ;;

      # run an experiment
      *)
        echo $exp
        # go back to main menu after starting experiment
        break 1
        ;;
    esac
  done
}

function runExperiment {
  bash "$fbrd/fb_cli/run_experiment.sh" "$1"
}

function runAllExperiments {
  msg "Will run all experiments on all platforms, this will take some time...."
  echo "experiments: $(listExperiments)"
  msg "Would you like to proceed? [yes/no]"
  read -n 3 -r ; echo
  if [[ $REPLY =~ ^yes$ ]]; then
    for exp in $(listExperiments) ; do
      bash "$fbrd/fb_cli/run_experiment.sh" "$exp"
    done
  else
    errmsg "Aborting ..."
  fi

}

function runExperimentLocally {
  pmsg "Running experiment: $1 locally with OpenFaas on Minikube ..."
  bash "$fbrd/fb_cli/run_experiment_local.sh" "$1"
}

function rerunLastExperimentLocally {
  runExperimentLocally $1
}

function echoOpenfaasMinikubePassword {
  kubectl \
    get secret \
    -n openfaas \
    basic-auth \
    -o jsonpath="{.data.basic-auth-password}" \
    | base64 --decode \
    ; echo
}


function checkIfOrchestrator {
  [ "$HOSTNAME" = "orchestrator" ] \
    && return 0 \
    || errmsg "Please do not run experiments locally, ssh to the orchestrator server and run the experiments from the server." && exit
}

# TODO refactor
function runExperimentWrapper {
  checkIfOrchestrator
  # choose experiment name to run, if cancelledd will be an empty string
  exp=$(chooseExperiment)
  # break out if cancelled
  [ -z "$exp" ] && errmsg "Cancelled." && break 1
  # actually run the chosen experiment
  runExperiment "$exp"
}

# TODO refactor
function runAllExperimentsWrapper {
  checkIfOrchestrator
  runAllExperiments
}

# ==================================

function devInteractive {
  echo "Options for running experiments locally for development:"
  select dev_opt in $dev_options ; do
    case $dev_opt in

      run_experiment_locally)
        dev_exp=$(chooseExperiment)
        # break out if cancelled
        [ -z "$dev_exp" ] && msg "Cancelled." && break 1
        runExperimentLocally "$dev_exp"
        ;;

      rerun_last_experiment_locally)
        if [ -z "$dev_exp" ] ; then
          msg "Have not run any experiment locally yet, choose one to run..."
          dev_exp=$(chooseExperiment)
          # break out if cancelled
          [ -z "$dev_exp" ] && msg "Cancelled." && break 1
          runExperimentLocally "$dev_exp"
        else
          rerunLastExperimentLocally $dev_exp
        fi
        ;;

      echo_minikube_openfaas_password)
        echoOpenfaasMinikubePassword
        ;;

      fix_minikube_port_forward)
        fixMinikubePortForward
        ;;

      start_minikube)
        startMinikube
        ;;

      stop_minikube)
        stopMinikube
        ;;

      minikube_openfaas_status)
        pmsg "Minikube Status"
        minikube status
        pmsg "OpenFaas on Minikube Status, if faas-cli returns an error, run the fix_minikube_port_forward option."
        faas-cli list
        ;;

      bootstrap_openfaas_locally)
        bootstrapOpenfaasLocally
        ;;

      teardown_openfaas_locally)
        teardownOpenfaasLocally
        ;;

      # go back to previous menu
      main_menu)
        break 1
        ;;

      *)
        echo "Press return to see options ..."
        ;;

    esac
  done
}

function runInteractively {
  banner
  # interactively choose command
  select opt in $options; do
    case "$opt" in

      run_experiment)
        runExperimentWrapper
        ;;

      run_all_experiments)
        runAllExperimentsWrapper
        ;;

      generate_report)
        # TODO
        echo "not implemented yet"
        ;;

      create_experiment)
        createExperiment
        ;;

      update_experiment_infra_templates)
        updateExperimentInfraTemplates
        ;;

      first_time_infrastructure_bootstrap)
        firstTimeInfrastrutureBootstrap
        ;;

      destroy_permanent_infrastructure)
        destroyPermanentInfrastructure
        ;;

      clear_screen)
        clear
        ;;

      ssh_orchestrator)
        sshOrchestrator
        ;;

      ssh_db_server)
        sshDBServer
        ;;

      dev_options)
        devInteractive
        ;;

      exit)
        exit
        ;;

      *)
        echo "Press return to see options ..."
        ;;

    esac
  done
}

function usage {
  msg "Options:"
  msg "-i | --interactive : run in interactive mode"
  msg "-d | --dev : run in interactive development mode"
  msg "-l | --list-experiments : list available experiments"
  msg "-r | --run-experiment [experiment name] : run experiment with provided [experiment name]"
  msg "\tyou may pass multiple experiments to be run in parallel"
  msg "-ra | --run-all-experiments : run all experiments"
  msg "--generate-report : generate report based from result {not implemented yet}"
  msg "--create-experiment [experiment name] : create new experiment with provided [experiment name]"
  msg "--update-experiment-infrastructure-templates : update infrastructure templates for existing experiments"
  msg "--bootstrap-permamnent-infrastructure : create the orchestrator and database/log servers"
  msg "--destroy-permanent-infrastructure : destroy the orchestrator and database/log servers"
  msg "--ssh-orchestrator : ssh to the orchestrator server"
  msg "--ssh-db-server : ssh to the database/log server"
  msg "-h | --help : print this help message"
  echo
}

function banner {
  # raise the banner...
  cat "$fbrd/fb_cli/banner"
  msg "Command-line tool for controlling the faas-benchmarker framework."
  echo
}

function printHelp {
  banner
  usage
}

# ==================================

# check that all env vars are set
bash "$fbrd/fb_cli/check_env_vars.sh" && exit

# commands that can be issued
options="
run_experiment
run_all_experiments
generate_report
create_experiment
update_experiment_infra_templates
first_time_infrastructure_bootstrap
destroy_permanent_infrastructure
dev_options
clear_screen
"

# add ssh commands if not on orchestrator server
if [ "$HOSTNAME" != "orchestrator" ] ; then
  options+=" ssh_orchestrator ssh_db_server"
fi

# make sure exit is always the last option...
options+=" exit"

dev_options="
run_experiment_locally
rerun_last_experiment_locally
echo_minikube_openfaas_password
fix_minikube_port_forward
start_minikube
stop_minikube
minikube_openfaas_status
bootstrap_openfaas_locally
teardown_openfaas_locally
main_menu
"

# ==================================
# parse postional options and arguments


if [[ ! $# -gt 0 ]] ; then

  # if there are no options, then print help
  printHelp

else

  # parse option/argument pairs

  POSITIONAL=()
  while [[ $# -gt 0 ]] ; do
    KEY="$1"
    case $KEY in

      -i | --interactive)
        runInteractively
        ;;

      -d | --dev)
        devInteractive
        ;;

      -le | --list-experiments)
        listExperiments
        exit
        ;;

      -r | --run-experiment)
        EXPERIMENT="$2"
        checkThatExperimentExists "$EXPERIMENT" \
          && runExperiment "$EXPERIMENT"
        shift
        shift
        ;;

      -ra | --run-all-experiments)
        runAllExperiments
        exit
        ;;

      --generate-report)
        generateReport
        exit
        ;;

      --update-experiment-infrastructure-templates)
        updateExperimentInfraTemplates
        exit
        ;;

      --bootstrap-permamnent-infrastructure)
        firstTimeInfrastrutureBootstrap
        exit
        ;;

      --destroy-permanent-infrastructure)
        destroyPermanentInfrastructure
        exit
        ;;

      --ssh-orchestrator)
        sshOrchestrator
        exit
        ;;

      --ssh-db-server)
        sshDBServer
        exit
        ;;

      -h | --help)
        printHelp
        exit
        ;;

      *)
        errmsg "Unknown option ..."
        usage
        exit
        ;;

    esac
  done
fi
