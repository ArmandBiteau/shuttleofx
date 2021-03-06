#!/usr/bin/python
from flask import Flask, request, jsonify, send_file, abort
import os
import uuid
import atexit
import logging
import tempfile
import ConfigParser
import multiprocessing

import renderScene

configParser =  ConfigParser.RawConfigParser()
configParser.read('render.cfg')

g_app = Flask(__name__, static_folder='', static_url_path='')

# list of all computing renders
g_renders = {}
g_rendersSharedInfo = {}

# Pool for rendering jobs
# processes=None => os.cpu_count()
g_pool = multiprocessing.Pool(processes=4)
g_enablePool = False

# Manager to share rendering information
g_manager = multiprocessing.Manager()

# list of all rendered resources
g_listImg = {}

currentAppDir = os.path.dirname(__file__)

tmpRenderingPath = os.path.join(currentAppDir, configParser.get('RENDERED_IMAGE', 'renderedImagesDirectory'))
if not os.path.exists(tmpRenderingPath):
    os.makedirs(tmpRenderingPath)

resourcesPath = os.path.join(currentAppDir, configParser.get('RESOURCES', 'resourcesDirectory'))
if not os.path.exists(resourcesPath):
    os.makedirs(resourcesPath)

# TODO: replace multiprocessing with https://github.com/celery/billiard to have timeouts in the Pool.

@g_app.route('/render', methods=['POST'])
def newRender():
    '''
    Create a new render and return graph informations.
    '''
    global g_renders, g_pool

    datas = request.json
    renderID = str(uuid.uuid1())

    _, tmpFilepath = tempfile.mkstemp(prefix='tuttle_', suffix=".png", dir=tmpRenderingPath)
    resourcePath = os.path.basename(tmpFilepath)

    newRender = {}
    newRender['id'] = renderID
    newRender['outputFilename'] = resourcePath
    newRender['scene'] = datas
    g_renders[renderID] = newRender

    g_app.logger.debug('new resource is ' + resourcePath)

    renderSharedInfo = g_manager.dict()
    renderSharedInfo['status'] = 0
    g_rendersSharedInfo[renderID] = renderSharedInfo

    if g_enablePool:
        g_pool.apply(renderScene.computeGraph, args=[renderSharedInfo, newRender, tmpFilepath])
    else:
        renderScene.computeGraph(renderSharedInfo, newRender, tmpFilepath)
    
    return jsonify(render=newRender)


@g_app.route('/progress/<renderID>', methods=['GET'])
def getProgress(renderID):
    '''
    Return render progress.
    '''
    return str(g_rendersSharedInfo[renderID]['status'])


@g_app.route('/render', methods=['GET'])
def getRenders():
    '''
        Returns all renders in JSON format
    '''
    totalRenders = {"renders": g_rendersSharedInfo}
    return jsonify(**totalRenders)


@g_app.route('/render/<renderID>', methods=['GET'])
def getRenderById(renderID):
    '''
    Get a render by id in json format.
    '''

    for key, render in g_renders.iteritems():
        if renderID == key:
            return jsonify(render=render)
    g_app.logger.error('id '+ renderID +" doesn't exists")
    abort(404)


@g_app.route('/render/<renderId>/resource/<resourceId>', methods=['GET'])
def resource(renderId, resourceId):
    '''
    Returns file resource by renderId and resourceId.
    '''
    if os.path.isfile( os.path.join(tmpRenderingPath, resourceId) ):
        return send_file( os.path.join(tmpRenderingPath, resourceId) )
    else:
        logging.error(tmpRenderingPath + resourceId + " doesn't exists")
        abort(404)


@g_app.route('/render/<renderID>', methods=['DELETE'])
def deleteRenderById(renderID):
    '''
    Delete a render from the render array.
    TODO: needed?
    TODO: kill the corresponding process?
    '''
    if renderID not in g_renders:
        g_app.logger.error('id '+renderID+" doesn't exists")
        abort(400)
    del g_renders[renderID]


@g_app.route('/resources/', methods=['POST'])
def addResource():
    '''
    Upload resource file on the server and returns id and uri.
    '''
    global g_listImg

    uid = str(uuid.uuid1())
    img = request.data
    ext = request.headers.get("Content-Type").split('/')[1]

    imgFile = "/resources/" + uid + "." + ext

    f = open("../resources/" + uid + "." + ext, 'w')
    f.write(img)
    f.close()

    objectId = {
        'id': uid,
        'uri': imgFile
    }

    g_listImg[uid] = imgFile

    return jsonify(**objectId)


@g_app.route('/resources/<resourceId>', methods=['GET'])
def getResource(resourceId):
    '''
    Returns resource file.
    '''
    if os.path.isfile("../resources/" + resourceId):
        return send_file("../resources/" + resourceId)
    abort(404)
    return

@g_app.route('/resources/', methods=['GET'])
def getResourcesDict():
    '''
     Returns a list of all resources on server.
    '''
    return jsonify(files=g_listImg)

def getAllResources():
    '''
    Fill the list of images with all resources path on the server.
    '''
    global g_listImg
    for image in os.listdir(str(resourcesPath)):
        _id = str(uuid.uuid4())
        g_listImg[_id] = str(resourcesPath) + str(image)


@atexit.register
def quit():
    '''
    Close processes and quit pool at exit.
    '''
    g_pool.close()
    g_pool.terminate()
    g_pool.join()

if __name__ == "__main__":
    getAllResources()
    g_app.run(host=configParser.get("APP_RENDER", "host"), port=configParser.getint("APP_RENDER", "port"), debug=True)
