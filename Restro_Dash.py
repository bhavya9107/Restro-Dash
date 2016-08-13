from flask import Flask,render_template,request,url_for,redirect,flash,jsonify

app=Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem, User

from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID= json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('postgres://dspbwegueaizep:J1p7AmtmyNjzYUgwoYjKI0H1O8@ec2-23-21-234-218.compute-1.amazonaws.com:5432/ddb5gkevc1sdo5')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state=''.join(random.choice(string.ascii_uppercase+string.digits)for x in xrange(32))
    login_session['state']=state
    return render_template('login.html', STATE = state,login_session=login_session)


    
@app.route('/restaurants/<int:restaurant_id>/menu.json')
def jsonMenu(restaurant_id):
    restaurant=session.query(Restaurant).filter_by(id=restaurant_id).one()
    items=session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return jsonify(MenuItem=[i.serialize for i in items])

@app.route('/restaurant.json')
def jsonRes():
    results = session.query(Restaurant).order_by(Restaurant.id).all()
    return jsonify(Restaurant=[i.serialRes for i in results])

@app.route('/')
def first():
    results = session.query(Restaurant).order_by(Restaurant.id.desc()).limit(10).all()
    creator = -1
    i = 1
    return render_template('homepage.html',results=results, i=i,login_session=login_session)

@app.route('/restaurants/<int:restaurant_id>/new', methods=['GET','POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    else:
	   restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	   if request.method == 'POST':
		  newItem = MenuItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], course = request.form['course'], restaurant_id = restaurant_id,user_id=restaurant.user_id)
		  session.add(newItem)
		  session.commit()
		  flash(newItem.name+" is Created Successfully")
		  return redirect(url_for('RestaurantMenu', restaurant_id = restaurant_id))
	   else:
		  return render_template('newMenuItem.html', restaurant_id = restaurant_id,restaurant=restaurant,login_session=login_session)

@app.route('/restaurants/new', methods=['GET','POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    else:
       if request.method == 'POST':
          req = session.query(Restaurant).filter_by(name = request.form['name']).first()
          if req :
            flash(request.form['name']+" already in usage")
            return redirect(url_for('newRestaurant'))
          else:
            newRes = Restaurant(name = request.form['name'],user_id= login_session['user_id'])
            user_id= login_session['user_id']
            session.add(newRes)
            session.commit()
            flash(newRes.name+" is Created Successfully")
            return redirect(url_for('first'))
       else:
          return render_template('newrestaurant.html',login_session=login_session)

@app.route('/restaurants/<int:restaurant_id>/<int:MenuID>/edit', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, MenuID):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedItem = session.query(MenuItem).filter_by(id = MenuID).one()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit()
        flash(editedItem.name+" is edited Successfully")
        return redirect(url_for('RestaurantMenu', restaurant_id = restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id = restaurant_id, MenuID = MenuID, item = editedItem,restaurant=restaurant,login_session=login_session)

@app.route('/restaurants/<int:restaurant_id>/delete_restaurant/',methods=['GET','POST'])
def deleteRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    results = session.query(Restaurant.name,Restaurant.id).order_by(Restaurant.name).all()
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if restaurant.user_id != login_session['user_id']:
        return '''<script>function myFunction() 
        {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete');}
        </script><body onload='myFunction()'>'''
    
    if request.method=='GET':
        return render_template('deleterestaurant.html', restaurant = restaurant,login_session=login_session)
    if request.method=='POST':
        session.delete(restaurant)
        session.commit()
        flash(restaurant.name+" is successfully deleted ;)")
        return redirect(url_for('first'))

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/JSON')
def MenuItemJson(restaurant_id,menu_id):
    restaurant=session.query(Restaurant).filter_by(id=restaurant_id).one()
    items=session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=items.serialize)
    
@app.route('/restaurants/<int:restaurant_id>/')
def RestaurantMenu(restaurant_id):
    restaurant=session.query(Restaurant).filter_by(id=restaurant_id).one()
    items=session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    creator = getUserInfo(restaurant.user_id)
    if 'username' not in login_session or creator.id!=login_session['user_id']:
        return render_template('menupublic.html', restaurant=restaurant, items=items, creator=creator,login_session=login_session)
    else:
        return render_template('menu.html', restaurant=restaurant, items=items, creator=creator,login_session=login_session)

@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete_item/',methods=['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('RestaurantMenu', restaurant_id=restaurant.id))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete , restaurant_id = restaurant.id,login_session=login_session)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '''
    <div class="mdl-card mdl-shadow--2dp" style="padding: 12px;">
    <h3>Welcome,'''
    output += login_session['username']
    output += '!</h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"></div>'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response=make_response(json.dumps('Invalid State parameter'),401)
        response.headers['Content-Type']='application/json'
        return response
    code=request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id=getUserID(login_session['email'])
    if not user_id:
        user_id=createUser(login_session)
    login_session['user_id']= user_id
    output = ''
    output += '''
    <div class="mdl-card mdl-shadow--2dp" style="padding: 12px;">
    <h3>Welcome,'''
    output += login_session['username']
    output += '!</h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"></div>'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    if login_session:
        access_token = login_session['credentials']
        print 'In gdisconnect access token is' + access_token
        print 'User name is: ' 
        print login_session['username']
        if access_token is None:
            print 'Access Token is None'
            response = make_response(json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        url = 'https://accounts.google.com/o/oauth2/revoke?token=' + access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        print 'result is '
        print result
        if result['status'] == '200':
            del login_session['credentials'] 
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            
            flash("Come Back soon here")
            return redirect(url_for('first'))
        else:
        
            response = make_response(json.dumps('Failed to revoke token for given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            return response
    else:
        return "no user signed-In"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('first'))
    else:
        flash("You were not logged in")
        return redirect(url_for('first'))

def getUserInfo(user_id):
    user=session.query(User).filter_by(id=user_id).first()
    return user

def createUser(login_session):
    newUser=User(name=login_session['username'], 
        email=login_session['email'], picture= login_session['picture'])
    session.add(newUser)
    session.commit()
    user= session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

   
#if __name__=='__main__':
app.secret_key="you are mad langoor"
app.debug= False
#app.run(host="0.0.0.0",port=5555) 

