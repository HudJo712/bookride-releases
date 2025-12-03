import jenkins.model.*
import jenkins.install.InstallState
import java.util.concurrent.TimeUnit

def plugins = [
  'git','git-client','workflow-job','workflow-cps','workflow-api',
  'workflow-durable-task-step','workflow-scm-step',
  'credentials','plain-credentials','ssh-credentials','credentials-binding',
  'cloudbees-folder','antisamy-markup-formatter','structs','workflow-step-api',
  'token-macro','build-timeout','timestamper','script-security','junit',
  'matrix-project','resource-disposer','ws-cleanup','ant','workflow-support',
  'workflow-cps-global-lib','workflow-multibranch','branch-api','display-url-api',
  'mailer','workflow-basic-steps','gradle','pipeline-milestone-step',
  'snakeyaml-api','jackson2-api','pipeline-input-step','pipeline-stage-step',
  'pipeline-graph-analysis','pipeline-rest-api','pipeline-stage-view',
  'pipeline-build-step','pipeline-model-api','pipeline-model-extensions',
  'pipeline-stage-tags-metadata','pipeline-model-definition',
  'lockable-resources','okhttp-api','github-api','github','github-branch-source',
  'pipeline-github-lib','subversion','ssh-slaves','matrix-auth','pam-auth','ldap',
  'email-ext','jsch','scm-api'
]

def j = Jenkins.instance
j.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)
def uc = j.updateCenter
uc.updateAllSites()

plugins.each { id ->
  if (j.pluginManager.getPlugin(id) == null) {
    def p = uc.getPlugin(id)
    if (p) {
      println "Installing ${id}"
      p.deploy(true).get(15, TimeUnit.MINUTES) // block until done
    } else {
      println "Plugin ${id} not found in update center"
    }
  } else {
    println "Plugin ${id} already installed"
  }
}
j.save()
