import jenkins.model.Jenkins

def required = ['credentials', 'plain-credentials']
def j = Jenkins.instance
def pm = j.pluginManager

// wait briefly for credentials plugins to be active
int attempts = 60
while (attempts-- > 0 && !required.every { pm.getPlugin(it)?.isActive() }) {
  println "Waiting for credentials plugins to load..."
  Thread.sleep(2000)
}
if (!required.every { pm.getPlugin(it)?.isActive() }) {
  println "Skipping webhook credential creation; credentials plugins not loaded."
  return
}

// load classes via plugin classloader
def cl = pm.uberClassLoader
def CredentialsScope     = cl.loadClass('com.cloudbees.plugins.credentials.CredentialsScope')
def Domain               = cl.loadClass('com.cloudbees.plugins.credentials.domains.Domain')
def StringCredentialsImpl= cl.loadClass('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl')
def Secret               = cl.loadClass('hudson.util.Secret')

// set values (use env vars or replace placeholders)
def credId   = 'stage-webhook'
def webhook  = System.getenv('STAGE_WEBHOOK_URL')

if (!webhook) {
  println "Skipping webhook credential creation; STAGE_WEBHOOK_URL not provided."
  return
}

def store = j.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
if (!store.getCredentials(Domain.global()).any { it.id == credId }) {
  def cred = StringCredentialsImpl
               .getConstructor(CredentialsScope, String, String, Secret)
               .newInstance(CredentialsScope.GLOBAL, credId, 'Stage webhook URL', Secret.fromString(webhook))
  store.addCredentials(Domain.global(), cred)
  println "Created credential ${credId}"
} else {
  println "Credential ${credId} already exists"
}
