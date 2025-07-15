## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_0c9c1ae.sh

### analysis
Concretization + dataflow analysis may eliminate the assumption annotation, but it is very difficult and complex. The pipeline depends on $responseHeaders, which is depends on the file $HTTP_HEADER. the file $HTTP_HEADER is written by the command `$_WGET -S -O - --user-agent="$USER_AGENT" --header "$_H5" --header "$_H4" --header "$_H3" --header "$_H2" --header "$_H1" --method $httpmethod --body-data="$body" "$_post_url" 2>"$HTTP_HEADER"`. `$_WGET` is expanded to `wget` with some flags, which may be determined by concretization, but it is involved in some control flow, although the control flow is deterministic by concretization. $body is "" in this related call. Headers (e.g., $_H5) can be found in another script and is determined in this related call. Maybe user can provide another kind of annotation (e.g., static) before the control flow, and the system can concretize contextual information with the annotation.

Assertion can be eliminated by dataflow analysis.

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow
3. need a simple model of side effect
4. need concretization with internet access

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_2b5e2d4.sh

### analysis

The assumption can be eliminated by concretization with addional information from https://github.com/Neilpang/acme.sh/issues/1209, where $2 will be a nginx config file. The heuristic may be disabled because of the concretization.

### assumption
1. need concretization with addional information: $2 is a nginx config file; we need to provide the content of the file.
2. Enable the heuristic

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_04a609b.sh

### analysis

The assumption can be eliminated by concretization with addional information from https://github.com/Neilpang/acme.sh/issues/1209, where $2 will be a nginx config file. I still dont understand the fix. TODO: check the fix.

### assumption
1. need concretization with addional information: $2 is a nginx config file; we need to provide the content of the file.

### result
dont need assumption, dont know how to assert

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_5cc1d95.sh

### analysis
Concretization + dataflow analysis may eliminate the assumption annotation, but should handle control flow. The assertion is hard to assert.

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow

### result
dont need assumption, dont know how to assert

### note
Interesting. Seems to be a expressiveness problem.

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_6bdf689.sh

### analysis

### assumption
1. need concretization

### result
dont need assumption, dont know how to assert

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_14f3dbb.sh

### analysis

The output is hard to assert. It is always empty on every platform. However, after concretization, we cannot use the heuristic to catch the bug.

### assumption
1. need concretization
2. Enable the heuristic

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_15dded7.sh

### analysis
Assumption part is same as full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_0c9c1ae.sh. Assertion can be eliminated by dataflow analysis.

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow
3. need a simple model of side effect
4. need concretization with internet access

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_37d22a1.sh

### analysis

Assumption part is same as full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_0c9c1ae.sh. Assertion can be eliminated by heuristic.

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow
3. need a simple model of side effect
4. need concretization with internet access
5. Enable the heuristic

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_48f02fb.sh

### analysis
Assumption part is same as full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_0c9c1ae.sh. Assertion can be eliminated by dataflow analysis.

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow
3. need a simple model of side effect
4. need concretization with internet access

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_70f4cad.sh

### analysis

Assumption part is same as full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_0c9c1ae.sh. Assertion can be eliminated by dataflow analysis.

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow
3. need a simple model of side effect
4. need concretization with internet access

dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_72af092.sh

### assumption
1. need concretization with addional information: $_outcsr is a result of openssl command; we need to provide the content of this

### result
dont need assumption, need assertion

### note
Interesting.

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_90b65c6.sh

### analysis
assert the output should use single quote to avoid globing

### assumption
1. need concretization with addional information: $domainlist is a result of idn command; we need to provide the content of this

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/acme.sh_acme_06580bf.sh

### assumption
1. need concretization with addional information: $2 is a nginx config file; we need to provide the content of the file.
2. Enable the heuristic

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/advanced_Scripts_chronometer.sh_chronometer_dac27f1.sh

### assumption

1. need concretization

### result

dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/advanced_Scripts_list.sh_list_1bf43b0.sh

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/advanced_Scripts_list.sh_list_2061daa.sh

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/advanced_Scripts_piholeDebug.sh_piholeDebug_5cebcea.sh

### assumption
1. need concretization

dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/advanced_Scripts_piholeDebug.sh_piholeDebug_36937b1.sh

### analysis
the assertion is "assert contains"

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/aliases_available_git.aliases.bash_git.aliases_2a23598.bash

### assumption
1. need concretization

dont need assumption, dont know how to assert

full_benchmark/github_repos_commits/collected/pre_commit/automated install_basic-install.sh_basic-install_8ee2bde.sh

### analysis
the assertion is "assert contains"

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/automated install_basic-install.sh_basic-install_466fd79.sh

### analysis
variable in the grep pattern, which is not supported now. The pipeline still seems buggy.

### assumption
1. need concretization

### result
dont need assumption, dont know how to assert

## full_benchmark/github_repos_commits/collected/pre_commit/automated install_basic-install.sh_basic-install_523f650.sh

### assumption
1. need concretization with internet access

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/automated install_basic-install.sh_basic-install_9212eea.sh

### analysis
the assertion is "assert contains"

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/dnsapi_dns_1984hosting.sh_dns_1984hosting_0ab1439.sh

### assumption
1. need dataflow analysis
2. need concretization with complicated control flow
3. need a simple model of side effect
4. need concretization with internet access
5. Enable the heuristic

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/functions_vcs.zsh_vcs_cb5d33a.zsh

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/install_fix-framework-text-scaling.sh_fix-framework-text-scaling_9b08be1.sh

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/install.sh_install_67be567.sh

### assumption
1. need dataflow analysis

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/lib_dirspersist.zsh_dirspersist_21e2a91.zsh

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/lib_git.zsh_git_27fff27.zsh

### assumption
1. need dataflow analysis
2. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/lib_git.zsh_git_6774fb3.zsh

### assumption
1. need dataflow analysis
2. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/lib_git.zsh_git_8890450.zsh

### assumption
1. need dataflow analysis
2. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/lib_helpers.bash_helpers_1e77c26.bash

### analysis
the awk pattern is not valid. Maybe out of scope.

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/modes_stealth.sh_stealth_ca08f79.sh

### analysis
command argument usage is wrong. Maybe out of scope.

### assumption
1. need concretization

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/nvm.sh_nvm_6dc602b.sh

### assumption
1. need concretization with complicated control flow
2. need dataflow analysis

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/nvm.sh_nvm_578a601.sh

### assumption
1. need concretization with complicated control flow
2. need dataflow analysis

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/nvm.sh_nvm_b59ecb9.sh

### assumption
1. need concretization with complicated control flow
2. need dataflow analysis

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/nvm.sh_nvm_cb87c31.sh

### assumption
1. need concretization with complicated control flow
2. need dataflow analysis

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/openvpn-install_Nyr_6d89279.sh

### assumption
1. need concretization
2. need dataflow analysis

### result
dont need assumption, dont need assertion

### note
Interesting.

## full_benchmark/github_repos_commits/collected/pre_commit/openvpn-install.sh_openvpn-install_aca3b4a.sh

### assumption
1. need concretization
2. need dataflow analysis

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/openvpn-install.sh_openvpn-install_d324165.sh

### analysis
the assertion is "assert contains"

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_available_base.plugin.bash_base.plugin_e687857.bash

### analysis
may not need assertion (the output is a IP address, and this is a function output)

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_battery_battery.plugin.zsh_battery.plugin_15a0374.zsh

### analysis
may not need assertion (the output is a IP address, and this is a function output)

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_composer_composer.plugin.zsh_composer.plugin_8b5950b.zsh

### analysis
the awk pattern is not valid. Maybe out of scope.

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_git_git.plugin.zsh_git.plugin_d60522c.zsh

### analysis
the grep pattern is not valid. Maybe out of scope.

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_mix-fast_mix-fast.plugin.zsh_mix-fast.plugin_bf87e99.zsh

### analysis
command argument usage is wrong. Maybe out of scope.

### assumption
1. need concretization

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_n98-magerun_n98-magerun.plugin.zsh_n98-magerun.plugin_de76905.zsh

### analysis
the awk pattern is not valid. Maybe out of scope.

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/plugins_rake-fast_rake-fast.plugin.zsh_rake-fast.plugin_c56fa99.zsh

### assumption
1. need concretization

### result
dont need assumption, need assertion

full_benchmark/github_repos_commits/collected/pre_commit/plugins_rvm_rvm.plugin.zsh_rvm.plugin_d20c111.zsh

### analysis
command argument usage is wrong. Maybe out of scope.

### result
dont need assumption, dont need assertion

full_benchmark/github_repos_commits/collected/pre_commit/plugins_svn_svn.plugin.zsh_svn.plugin_e2f7623.zsh

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/themes_base.theme.bash_base.theme_24c1cd1.bash

### assumption
1. need dataflow analysis
2. need models for different platforms

### result
dont need assumption, dont need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/themes_base.theme.bash_base.theme_70e4ac9.bash

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/themes_base.theme.bash_base.theme_ba02955.bash

### assumption
1. need concretization

### result
dont need assumption, need assertion

## full_benchmark/github_repos_commits/collected/pre_commit/wireguard-install.sh_wireguard-install_e05e633.sh

### assumption
1. need concretization

### result
dont need assumption, need assertion


## Result

* All 53 pipelines: No assumption annotations with some system level assumptions.

  - 26 pipelines: Annotations can be eliminated directly via command execution and dataflow analysis.

  - 5 pipeline: Annotations can be eliminated via concretization with additional information.

  - 11 pipelies: Annotations can be eliminated via concretization with complicated control flow. The result is deterministic after concretization.



* 21 pipelines: No assertions are needed.

  - 7 of these have (non-trivial) syntactic issues and are likely out of scope.

  - 5 require heuristics that may conflict with concretization.

  - 9 can have their assertions eliminated via dataflow analysis.

* 5 pipelines: I dont know how to assert.

* 4 pipelines: Require an "assert_contains" assertion, which is difficult for developers to write correctly.