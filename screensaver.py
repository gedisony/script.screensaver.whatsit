#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016 Edison Yau (gedisony@gmail.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import random
import os, sys
import urlparse

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

import xbmc
import xbmcaddon
import xbmcvfs
import re
import urllib
#import csv
import resources.lib.requests_cache 


import threading
from Queue import Queue, Empty, Full

reload(sys)
sys.setdefaultencoding("utf-8")

addon = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo('name')
ADDON_ID   = addon.getAddonInfo('id')
ADDON_PATH = addon.getAddonInfo('path')

SQLITE_FILE= xbmc.translatePath(  ADDON_PATH+"/resources/pokedex.sqlite" )

PROFILE_DIR=xbmc.translatePath("special://profile/addon_data/"+ADDON_ID)
CACHE_FILE=xbmc.translatePath(PROFILE_DIR+"/requests_cache")

PKMON_INDEX_FILE=xbmc.translatePath( PROFILE_DIR+"/pokemon_index.pickle" )
BGG_INDEX_FILE =xbmc.translatePath( PROFILE_DIR+"/bgg_index.pickle" )

facts_queue=Queue(maxsize=4)

#on a fresh install, the profile path is not yet created. Kodi will do this for our addon (after a user saves a setting)
#  the user will get an error because we cannot create our cache.sqlite file. 
#  we create it  
if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)
    #resources.lib.requests_cache.install_cache( CACHE_FILE, backend='memory' )  #will create a cache in memory
    #log('using memory for requests_cache file')
        
resources.lib.requests_cache.install_cache(CACHE_FILE, backend='sqlite', expire_after=604800 )  #cache expires after 7 days




def start(arg1, arg2):
    from resources.lib.screens import HorizontalSlideScreensaver2, pokeslide, bggslide
    from resources.lib.scrapers import bulbgarden, boardgamegeek

    ev = threading.Event()

#    bg=boardgamegeek()
    #bg.generate_random_slide();  return
#      
#     #create the boardgame id's file used in bgg 
#     #bgg.generate_index_from_web() ; return
      #bg.get_game_list(1); return
#     
#     #used for listing category ID & mechanic id for strings.po
#     #bgg.get_bg_categories()
#     
#     c = bgg.generate_random_slide() ;log('    *test*' + repr( c )  ) ; return
#     return
# 
#   
# #     h= bgg.hot_items('boardgame')
# #     for count, i in enumerate(h):
# #         log( repr(count) + ' ' + repr( i.name ) + i.thumbnail )
#       

    work_q = Queue()
    

    try:
        if arg1=='pokemon':
            bg=bulbgarden()
            bg.load_data()
            t = Worker(work_q, facts_queue, bg)
            s=pokeslide(ev,facts_queue,t)
        else:
            bg=boardgamegeek()
            bg.load_data()
            
            #bg.get_hotness_list(30); return
            t = Worker(work_q, facts_queue, bg)
            s= bggslide(ev,facts_queue,t)
    except IOError as ioe:
        xbmc.executebuiltin('XBMC.Notification("%s","%s")' %(  localize(32901), localize(32902))  )
        raise
        
    #use this to recreate the pokemon data file.  {'name': u'Bulbasaur', 'generation': 1, 'shape': u'Quadruped', 'genus': u'Seed', 'type': u'grass,poison', 'id': 1} ,  {'name': u'Ivysaur', 'generation': 1, 'shape': u'Quadruped', 'genus': u'Seed', 'type': u'grass,poison', 'id': 2} ...
    #note: the pickle file is loaded during class._init_ comment out that part when generating a non-exisiting file 
    #bg.generate_index_from_db();return
     
    #testing code
    #bg.load_data()
    #bg.get_bulbapedia_entry(1)
    #c = bg.generate_random_slide() ;log('    *test*' + repr( c )  ) ; return
    
    #for i in range(20): c=bg.generate_random_slide() return

    #t.daemon = True
    t.start()
 
    xbmc.sleep(2000) #give the worker a headstart
    #s= pokeslide(ev,facts_queue)
    #s= bggslide(ev,facts_queue)

    try:
        s.start_loop()
    except Exception as e: 
        log("  EXCEPTION slideshow:="+ str( sys.exc_info()[0]) + "  " + str(e) )    

    s.close()
    del s
    #sys.modules.clear()

    log('    main done')
    t.join()

def action(arg1, arg2):
    
    cache_file=CACHE_FILE + '.sqlite'  #requests cache automatically adds .sqlite to its cache file
    addon.setSetting('clear_cache_file_result', '')
    
    if os.path.exists(cache_file):
        #log('cache file exists ' + cache_file )
        
        os.remove( cache_file )
        xbmc.sleep(2000)
        
        if not os.path.exists(cache_file):
            set_clear_cache_file_result(localize(32305))
            log('  delete cache file success' )
        else:
            log('  delete cache file failed' )
    else:
        log('cache file NOT exist ' + cache_file)
        set_clear_cache_file_result(localize(32306))
        
    pass

def build_index_file(arg1, arg2):
    from resources.lib.scrapers import bulbgarden, boardgamegeek
    log('Building index file %s' %(arg1)  )
    
    set_build_index_file_result('')
    
    try:
        if arg1=="bgg":
            bgg=boardgamegeek()
            #bg.generate_random_slide();  return
          
            #create the boardgame id's file used in bgg
            bgg.generate_index_from_web( set_build_index_file_result ) 
            
            #bgg.get_game_list(1)
            
    except Exception as e:
        #set_build_index_file_result(str(e))
        raise
    finally:
        #set_build_index_file_result(localize(32305)) #success
        pass
    
    return

def set_build_index_file_result(value):
    setSetting('bgg_index_button', value)

def set_clear_cache_file_result(value):
    setSetting('clear_cache_button', value)

def setSetting(setting_id, value):
    addon.setSetting(setting_id, value)
    pass
    
class ExitMonitor(xbmc.Monitor):
    def __init__(self, exit_callback):
        self.exit_callback = exit_callback

#     def onScreensaverDeactivated(self):
#         self.exit_callback()

    def abortRequested(self):
        self.exit_callback()

class Worker(threading.Thread):
    def __init__(self, q_in, q_out, slide_info_generator):
        threading.Thread.__init__(self)
        self.q_out = q_out
        self.q_in=q_in
        #self.ev=ev
        self.exit_monitor = ExitMonitor(self.stop)
        self.watchdog=20
        self.slide_info_generator=slide_info_generator
        #log('  p-init ' + str( self.work_list ))

    def stop(self):
        log('    #stop called')
        self.running=False
        self.exit_monitor = None

    def run(self):
        self.running = True
        while self.running:
            try:
                if self.q_out.full():
                    self.watchdog-=1
                    self.wait(3000)
                    #log('      #watchdog: %.2d output_queuesize(%.2d)' %(self.watchdog, self.q_out.qsize() ) )
                else:
                    self.do_work()
                    self.watchdog=40
                    #log('    #job processed %d %d' %(self.q_out.qsize(),self.watchdog ) )
                    self.wait(8000)
                 
            except Empty:  #input queue is enpty. 
                # Allow other stuff to run
                self.wait(1000)
                
            except Full:  #Queue.Full
                self.watchdog-=1
                
            except Exception as e:
                log("    #worker EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
            
            if self.watchdog<1:
                #failsafe machanism to prevent a worker thread running indefinitely
                log('    #worker thread self-terminating ')
                self.running=False

        log('    #worker thread done')

    def join(self, timeout=None):
        self.running=False
        log('    #join')
        super(Worker, self).join(timeout)
        
    def do_work(self):
        factlet=self.slide_info_generator.generate_random_slide()
        self.q_out.put( factlet ) #doesn't seem to throw exception when queue full.

    def wait(self, sleep_msec):
        # wait in chunks of 500ms to react earlier on exit request
        chunk_wait_time = 500 
        remaining_wait_time = sleep_msec   
        while remaining_wait_time > 0:
            if self.running == False:
                log('wait aborted')
                return
            if remaining_wait_time < chunk_wait_time:
                chunk_wait_time = remaining_wait_time
            remaining_wait_time -= chunk_wait_time
            xbmc.sleep(chunk_wait_time)



def localize(id):
    return addon.getLocalizedString(id).encode('utf-8')

def log(message, level=xbmc.LOGNOTICE):
    xbmc.log(ADDON_ID+":"+message, level=level)

if __name__ == '__main__':
    if len(sys.argv) > 1: 
        params=dict( urlparse.parse_qsl(sys.argv[1]) )
        #log("sys.argv[1]="+sys.argv[1]+"  ")        
    else: params={}

    mode   = params.get('mode', '')
    arg1    = params.get('arg1', '')
    arg2    = params.get('arg2', '') 
    
    log("----------------------")
    log("params="+ str(params))
    log("mode="+ mode)
    log("arg1="+ arg1) 
    log("arg2="+ arg2)
    log("-----------------------")
    
    if mode=='':mode='start'  #default mode is to list start page (index)

    script_modes = {'start'                 : start,
                    'build_index_file'      : build_index_file,
                    'action'                : action
                    }

    script_modes[mode](arg1,arg2)
