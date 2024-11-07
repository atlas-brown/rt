#!/bin/bash

scriptdir=$(dirname -- "$(realpath -- "$0")")
rootdir=$(dirname $scriptdir)
cd $rootdir >/dev/null

fix_experiment_path() {
  local exp=$1
  if [[ " $(basename $1) " =~ " ${exp} " ]]; then
    # just file name
    echo "experiments/${exp}"
  else
    echo "${exp}"
  fi
}

result_files=(
  "is_test_false_eval_results.txt"
  "is_test_false_eval_nbest_predictions.json"
  "is_test_true_eval_results.txt"
  "is_test_true_eval_nbest_predictions.json"
)

save_experiment_data() {
  local model_dir=$1; shift
  local results_dir=$1; shift
  local exp_name=$1; shift
  for file in ${result_files[@]}; do
    if [[ -f $model_dir/$file ]]; then
      echo "Saving $model_dir/$file $results_dir/${exp_name}_${file}"
      mv $model_dir/$file $results_dir/${exp_name}_${file}
    fi
  done
}

run_experiment() {
  local file=$1; shift
  local script_file="./src/mc-transformers/run_multiple_choice.py"
  if [[ -z ${DOCKERIZE} ]]; then
    inside_docker=""
  else
    inside_docker="nvidia-docker run ${docker_args[@]}"
  fi
  ${inside_docker} python3 ${script_file} $(python3 scripts/json_to_program_args.py $file)
}

results_dir='./results'
[[ ! -d $results_dir ]] && mkdir $results_dir

docker_img="quail-experiments"
docker_args="--shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 -v `pwd`:/workspace $docker_img"

echo "###### Starting experiments $(date)"
total_start_time=$(date -u +%s)

experiments=($@)
if [[ "${#experiments[@]}" -eq 1 ]]; then
  # if it is a filelist, parse it
  first_exp="${experiments[0]}"
  if [[ " ${first_exp##*.} " =~ " filelist " ]]; then
    IFS=$'\n' read -d '' -r -a experiments < $first_exp
    echo "* Read experiments from $first_exp:"
    echo "* ${experiments[@]}"
  fi
fi
for raw_exp in ${experiments[@]}; do
  exp=$(fix_experiment_path $raw_exp)
  echo "*********** $exp *************";
  run_experiment $exp
  # ToDo := Review this step
  # model_dir=$(sed -n 's/export OUTPUT_DIR=\(.*\)/\1/p' experiments/$exp);
  # exp_name=${exp%.*}
  # save_experiment_data $model_dir $results_dir $exp_name
  echo "********************************";
done

total_end_time=$(date -u +%s)
total_elapsed=$(python3 -c "print('{:.2f}'.format(($total_end_time - $total_start_time)/60.0 ))")
echo "###### End of experiments $(date) ($total_elapsed) minutes"

