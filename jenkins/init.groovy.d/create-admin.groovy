import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstanceOrNull()
if (instance == null) {
    println "Jenkins instance is not ready"
    return
}

def env = System.getenv()
def username = env['JENKINS_ADMIN_ID'] ?: 'admin'
def password = env['JENKINS_ADMIN_PASSWORD'] ?: 'admin123'

def realm = instance.getSecurityRealm()
if (!(realm instanceof HudsonPrivateSecurityRealm)) {
    realm = new HudsonPrivateSecurityRealm(false)
}

def user = realm.getUser(username)
if (user == null) {
    realm.createAccount(username, password)
    println "Created admin user '${username}'"
} else {
    try {
        user.delete()
        println "Deleted existing admin user '${username}' to reset password"
    } catch (Exception e) {
        println "Failed to delete existing admin user '${username}': ${e.message}"
    }
    realm.createAccount(username, password)
    println "Re-created admin user '${username}' with updated password"
}

instance.setSecurityRealm(realm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()
