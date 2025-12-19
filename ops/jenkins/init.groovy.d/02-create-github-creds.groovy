import jenkins.model.Jenkins

def required = ['credentials', 'plain-credentials']
def j = Jenkins.instance
def pm = j.pluginManager

// wait briefly for credentials plugin to be active
int attempts = 60
while (attempts-- > 0 && !required.every { pm.getPlugin(it)?.isActive() }) {
  println "Waiting for credentials plugins to load..."
  Thread.sleep(2000)
}
if (!required.every { pm.getPlugin(it)?.isActive() }) {
  println "Skipping credential creation; credentials plugins not loaded."
  return
}

// load classes via plugin classloader
def cl = pm.uberClassLoader
def CredentialsScope = cl.loadClass('com.cloudbees.plugins.credentials.CredentialsScope')
def Domain          = cl.loadClass('com.cloudbees.plugins.credentials.domains.Domain')
def UPCI            = cl.loadClass('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl')

// set values (use env vars or replace placeholders)
def credId = 'github-pat'
def ghUser = System.getenv('GITHUB_USER') ?: 'HudJo712'
def ghPAT  = System.getenv('GITHUB_PAT')

if (!ghPAT) {
  println "Skipping credential creation; GITHUB_PAT not provided."
  return
}

def store = j.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
if (!store.getCredentials(Domain.global()).any { it.id == credId }) {
  def cred = UPCI.getConstructor(CredentialsScope, String, String, String, String)
                 .newInstance(CredentialsScope.GLOBAL, credId, 'GitHub PAT', ghUser, ghPAT)
  store.addCredentials(Domain.global(), cred)
  println "Created credential ${credId}"
} else {
  println "Credential ${credId} already exists"
}
