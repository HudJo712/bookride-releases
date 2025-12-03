import jenkins.model.Jenkins

def required = [
  'git','git-client','workflow-job','workflow-cps','workflow-api',
  'workflow-durable-task-step','workflow-scm-step',
  'credentials','plain-credentials','ssh-credentials','credentials-binding'
]

def j = Jenkins.instance
def pm = j.pluginManager
def missing = required.findAll { pm.getPlugin(it) == null }
if (missing) {
  println "Skipping job creation; missing plugins: ${missing}"
  return
}

// load classes via plugin classloader
def cl = pm.uberClassLoader
def CredentialsScope = cl.loadClass('com.cloudbees.plugins.credentials.CredentialsScope')
def Domain          = cl.loadClass('com.cloudbees.plugins.credentials.domains.Domain')
def UPCI            = cl.loadClass('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl')
def GitSCM          = cl.loadClass('hudson.plugins.git.GitSCM')
def BranchSpec      = cl.loadClass('hudson.plugins.git.BranchSpec')
def WorkflowJob     = cl.loadClass('org.jenkinsci.plugins.workflow.job.WorkflowJob')
def CpsScmFlowDef   = cl.loadClass('org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition')

// settings – change these
def jobName    = 'Book and Ride – CI Pipeline'
def repoUrl    = 'https://github.com/HudJo712/bookride-releases.git'
def branchSpec = '*/main'
def scriptPath = 'Jenkinsfile'
def credId     = 'github-pat'
def ghUser     = 'HudJo712'
def ghPAT      = System.getenv("GITHUB_TOKEN")

// ensure credential
def store = j.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
if (!store.getCredentials(Domain.global()).any { it.id == credId }) {
  def cred = UPCI.getConstructor(CredentialsScope, String, String, String, String)
                 .newInstance(CredentialsScope.GLOBAL, credId, 'GitHub PAT for Book & Ride', ghUser, ghPAT)
  store.addCredentials(Domain.global(), cred)
  println "Created credential ${credId}"
} else {
  println "Credential ${credId} already exists"
}

// create/update job
def job = j.getItem(jobName) ?: j.createProject(WorkflowJob, jobName)
def scm = GitSCM.newInstance(GitSCM.createRepoList(repoUrl, credId),
                             [BranchSpec.newInstance(branchSpec)],
                             false, [], null, null, [])
def defn = CpsScmFlowDef.newInstance(scm, scriptPath)
defn.setLightweight(true)
job.setDefinition(defn)
job.save()
println "Created/updated job: ${jobName}"
