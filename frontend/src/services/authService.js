import { CognitoUserPool, AuthenticationDetails, CognitoUser } from 'amazon-cognito-identity-js';

const poolData = {
  UserPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
  ClientId: process.env.REACT_APP_COGNITO_CLIENT_ID
};

class AuthService {
  userPool = new CognitoUserPool(poolData);

  login(username, password) {
    return new Promise((resolve, reject) => {
      const authenticationData = { Username: username, Password: password };
      const authenticationDetails = new AuthenticationDetails(authenticationData);

      const userData = { Username: username, Pool: this.userPool };
      const cognitoUser = new CognitoUser(userData);

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (result) => {
          const accessToken = result.getAccessToken().getJwtToken();
          localStorage.setItem('token', accessToken);
          resolve(result);
        },
        onFailure: (err) => {
          reject(err);
        }
      });
    });
  }

  logout() {
    const cognitoUser = this.userPool.getCurrentUser();
    if (cognitoUser) {
      cognitoUser.signOut();
    }
    localStorage.removeItem('token');
  }

  isAuthenticated() {
    return localStorage.getItem('token') !== null;
  }
}

export default new AuthService();