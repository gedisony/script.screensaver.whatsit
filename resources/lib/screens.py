#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Original Work Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#     Modified Work Copyright (C) 2016 Edison Yau (gedisony@gmail.com)
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

import random, math
import sys
import threading
import Queue

import xbmc, xbmcaddon
from xbmcgui import ControlImage, WindowXMLDialog, ControlTextBox, ControlLabel, ListItem

from screensaver import log

import pprint

reload(sys)
sys.setdefaultencoding("utf-8")

addon = xbmcaddon.Addon()

ADDON_PATH = addon.getAddonInfo('path')

CHUNK_WAIT_TIME = 250
ACTION_IDS_EXIT = [9, 10, 13, 92]
ACTION_IDS_PAUSE = [12,68,79,229]   #ACTION_PAUSE = 12  ACTION_PLAY = 68  ACTION_PLAYER_PLAY = 79   ACTION_PLAYER_PLAYPAUSE = 229

class ffg_hangman(threading.Thread):
    #shows text one character at a time in a textbox control --not used
    def __init__(self, window, text_control, text ):
        threading.Thread.__init__(self)
        self.window=window
        self.control=text_control
        self.text=text

    def run(self):
        text=self.text
        te_t='_' * len(text)
        self.control.setText( te_t )
        te_tl = list(te_t)
        k=range( len(text) )
    
        random.shuffle(k)
        for c in k:
            xbmc.sleep(2000)
            te_tl[c]=text[c]
            self.control.setText( ''.join(te_tl) )
            log( ''.join(te_tl)  )   #+ ' .' + repr(c) + ' ='+ text[c:c+1])

class ScreensaverXMLWindow(WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        WindowXMLDialog.__init__(self, *args, **kwargs)
        self.exit_callback = kwargs.get("exit_callback")

    def onAction(self, action):
        action_id = action.getId()
        self.exit_callback(action_id)

class ScreensaverBase(object):
    MODE = None
    IMAGE_CONTROL_COUNT = 10
    FAST_IMAGE_COUNT = 0
    NEXT_IMAGE_TIME = 2000
    BACKGROUND_IMAGE = 'srr_blackbg.jpg'
    image_control_ids=[101,102,103,104,105]   #control id's defined in ScreensaverXMLWindow xml file
    
    pause_requested=False
    info_requested=False
    #image_controls_cycle=''

    def __init__(self, thread_event, facts_queue, worker_thread):
        #self.log('__init__ start')
        self.exit_requested = False
        self.background_control = None
        self.preload_control = None
        self.image_count = 0
        #self.image_controls = []
        #self.tni_controls = []
        self.global_controls = []
        self.exit_monitor = ExitMonitor(self.stop)
        self.facts_queue=facts_queue
        self.worker_thread=worker_thread
        self.init_xbmc_window()
        self.init_global_controls()
        self.load_settings()
        self.init_cycle_controls()
        self.stack_cycle_controls()
        #self.log('__init__ end')
    
    def init_xbmc_window(self):
        self.xbmc_window = ScreensaverXMLWindow( "slideshow02.xml", ADDON_PATH, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.setCoordinateResolution(5)
        self.xbmc_window.show()

    def init_global_controls(self):
        #self.log('  init_global_controls start')
        
        loading_img = xbmc.validatePath('/'.join((ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'srr_busy.gif' )))
        self.loading_control = ControlImage(576, 296, 128, 128, loading_img)
        self.preload_control = ControlImage(-1, -1, 1, 1, '')
        self.background_control = ControlImage(0, 0, 1280, 720, '')
        self.global_controls = [
            self.preload_control, self.background_control, self.loading_control
        ]
        self.xbmc_window.addControls(self.global_controls)
        #self.log('  init_global_controls end')

    def load_settings(self):
        pass

    def init_cycle_controls(self):
        #self.log('  init_cycle_controls start')
        #for i in xrange(self.IMAGE_CONTROL_COUNT):
        #    img_control = ControlImage(0, 0, 0, 0, '', aspectRatio=2)  #(values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
        #    txt_control = ControlTextBox(0, 0, 0, 0, font='font16')
#                     xbfont_left = 0x00000000
#                     xbfont_right = 0x00000001
#                     xbfont_center_x = 0x00000002
#                     xbfont_center_y = 0x00000004
#                     xbfont_truncated = 0x00000008
            #ControlLabel(x, y, width, height, label, font=None, textColor=None, disabledColor=None, alignment=0, hasPath=False, angle=0)
            #txt_control = ControlLabel(0, 0, 0, 0, '', font='font30', textColor='', disabledColor='', alignment=6, hasPath=False, angle=0)
            
            #self.image_controls.append(img_control)
        #    self.tni_controls.append([txt_control,img_control])
        #self.log('  init_cycle_controls end')
        pass
        
    def stack_cycle_controls(self):
        #self.log('stack_cycle_controls start')
        # add controls to the window in same order as image_controls list
        # so any new image will be in front of all previous images
        #self.xbmc_window.addControls(self.image_controls)
        #self.xbmc_window.addControls(self.text_controls)

        #self.xbmc_window.addControls(self.tni_controls[1])
        #self.xbmc_window.addControls(self.tni_controls[0])
        
        #self.log('stack_cycle_controls end')
        pass

    def start_loop(self):
        self.log('screensaver start_loop')
        
        #tni_controls_cycle= cycle(self.tni_controls)
        self.image_controls_cycle= cycle(self.image_control_ids)

        self.hide_loading_indicator()
        
        #pops the first one
        #self.log('get queue item')
        #factlet=self.facts_queue.get(block=True,timeout=5000)
        factlet=self.facts_queue.get()
        
        #self.log('  image_url_cycle.next %s' % image_url)
        
        while not self.exit_requested:
            #self.log('  using image: %s ' % ( repr(factlet) ) )
            self.log( '  using:' + pprint.pformat(factlet, indent=1) )

            #pops an image control
            
            image_control = self.image_controls_cycle.next()
            
            #if factlet:
            
            self.process_image(image_control, factlet)
            
            
            try:
                #if self.facts_queue.empty():
                #    self.wait()
                #    log('   queue empty %d' %(self.facts_queue.qsize())  )
                #else:
                factlet=self.facts_queue.get()
                    #log('   got next item from queue ' + factlet['name'])
                    #factlet=self.facts_queue.get(block=True,timeout=5000)  #doesn't throw exception if empty!
                    
            except Queue.Empty:
                self.log('   queue empty thrown')
                self.wait()
                
            self.wait()
            if self.image_count < self.FAST_IMAGE_COUNT:
                self.image_count += 1
            else:
                #self.preload_image(image_url)
                self.preload_image(factlet['image'])
                self.wait()
                
        self.log('start_loop end')
        
        #return the screensaver back
        #xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method":"Settings.setSettingValue", "params": {"setting":"screensaver.mode", "value" : "%s"} }' % saver_mode )


    def get_description_and_images(self, source):
        #self.log('get_images2')
        self.image_aspect_ratio = 16.0 / 9.0

        images = []

        if source == 'image_folder':
            path = SlideshowCacheFolder  #addon.getSetting('image_path')
            if path:
                images = self._get_folder_images(path)
        elif source == 'q':
            #implement width & height extract here.
            images=[[item[0], item[1],item[2], item[3], ] for item in self.facts_queue.queue]
            #texts=[item[0] for item in q.queue]
            #for i in images: self.log('   image: %s' %i)
            #self.log('    %d images' % len(images))

        return images


    #for movie, audio or tv shows
    def _get_json_images(self, method, key, prop):
        self.log('_get_json_images start')
        query = {
            'jsonrpc': '2.0',
            'id': 0,
            'method': method,
            'params': {
                'properties': [prop],
            }
        }
        response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
        images = [
            element[prop] for element
            in response.get('result', {}).get(key, [])
            if element.get(prop)
        ]
        self.log('_get_json_images end')
        return images

    def _get_folder_images(self, path):
        self.log('_get_folder_images started with path: %s' % repr(path))
        dirs, files = xbmcvfs.listdir(path)
        images = [
            xbmc.validatePath(path + f) for f in files
            if f.lower()[-3:] in ('jpg', 'png')
        ]
        #if addon.getSetting('recursive') == 'true':
        #    for directory in dirs:
        #        if directory.startswith('.'):
        #            continue
        #        images.extend(
        #            self._get_folder_images(
        #                xbmc.validatePath('/'.join((path, directory, '')))
        #            )
        #        )
        self.log('_get_folder_images ends')
        return images

    def hide_loading_indicator(self):
        bg_img = xbmc.validatePath('/'.join(( ADDON_PATH, 'resources', 'skins', 'Default', 'media', self.BACKGROUND_IMAGE )))
        #bg_img = self.BACKGROUND_IMAGE
        self.loading_control.setAnimations([(
            'conditional',
            'effect=fade start=100 end=0 time=500 condition=true'
        )])
        self.background_control.setAnimations([(
            'conditional',
            'effect=fade start=0 end=100 time=500 delay=500 condition=true'
        )])
        self.background_control.setImage(bg_img)

    def process_image(self, image_control_id, image_url):
        # Needs to be implemented in sub class
        raise NotImplementedError

    def preload_image(self, image_url):
        # set the next image to an unvisible image-control for caching
        #self.log('preloading image: %s' % repr(image_url))
        self.preload_control.setImage(image_url)
        #self.log('preloading done')

    def wait(self, msec=0):
        # wait in chunks of 500ms to react earlier on exit request
        
        chunk_wait_time = int(CHUNK_WAIT_TIME)
        remaining_wait_time = msec if msec > 0 else int(self.NEXT_IMAGE_TIME)
        #self.log('waiting for %d' %remaining_wait_time )
        while remaining_wait_time > 0:
            #self.log('waiting %d' %remaining_wait_time )
            if not self.worker_thread.isAlive():
                self.log('worker thread died')
                self.exit_requested=True

            if self.exit_requested:
                self.log('wait aborted')
                return
            
            if remaining_wait_time < chunk_wait_time:
                chunk_wait_time = remaining_wait_time
            remaining_wait_time -= chunk_wait_time
            xbmc.sleep(chunk_wait_time)

    def action_id_handler(self,action_id):
        #log('  action ID:' + str(action_id) )
        if action_id in ACTION_IDS_EXIT:
            #self.exit_callback()
            self.stop()
        if action_id in ACTION_IDS_PAUSE:  
            self.pause()          

        if action_id == 11: #xbmcgui.ACTION_SHOW_INFO:   
            self.info_requested=not self.info_requested            

    def stop(self,action_id=0):
        self.log('stop')
        self.exit_requested = True
        self.exit_monitor = None

    def pause(self):
        #pause disabled. too complicated(not possible?) to stop animation  
        #self.pause_requested = not self.pause_requested
        #self.log('pause %s' %self.pause_requested )
        pass

    def close(self):
        self.log('close')
        self.del_controls()

    def del_controls(self):
        #self.log('del_controls start')
        #self.xbmc_window.removeControls(self.img_controls)  
        #try: self.xbmc_window.removeControls(self.tni_controls[0]) #imageControls
        #except: pass
        #try: self.xbmc_window.removeControls(self.tni_controls[1]) #textBoxes
        #except: pass
        
        self.xbmc_window.removeControls(self.global_controls)
        self.preload_control = None
        self.background_control = None
        self.loading_control = None
        #self.tni_controls = []
        self.global_controls = []
        self.xbmc_window.close()
        self.xbmc_window = None
        #self.log('del_controls end')

    def log(self, msg):
        log(u'slideshow: %s' % msg)

class ExitMonitor(xbmc.Monitor):

    def __init__(self, exit_callback):
        self.exit_callback = exit_callback

    def onScreensaverDeactivated(self):
        self.exit_callback()

    def abortRequested(self):
        self.exit_callback()

class pokeslide(ScreensaverBase):
    BACKGROUND_IMAGE = '' #'srr_blackbg.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 0
    SPEED = 0.7
    IMAGE_ANIMATIONS = []

    def load_settings(self):
        self.SPEED = 1.0
        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))
        self.MAX_TIME = int(30000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(6000.0 / self.SPEED)

    def stack_cycle_controls(self):
        self.txt_group_control=self.xbmc_window.getControl(200)
        self.title_control=self.xbmc_window.getControl(201)
        self.desc_control=self.xbmc_window.getControl(202)
        self.title2_control=self.xbmc_window.getControl(203)
        self.title3_control=self.xbmc_window.getControl(204)

    def process_image(self, image_control_id, factlet ):

        t=self.MAX_TIME
        
        #del a[:]
        centery=920 #used for rotate animation to flip image
        end_x=560
        end_y=0
        self.txt_group_control.setVisible(False)
        self.txt_group_control.setPosition(0, 0)
        
        #randomize wether image will be on left side of screen or on right
        if random.getrandbits(1):
            centery=360
            end_x=0
            self.txt_group_control.setPosition(720, 0)
            
        self.txt_group_control.setAnimations( self.random_textcontrol_animations() )    
            
        self.IMAGE_ANIMATIONS=[]
        self.IMAGE_ANIMATIONS.extend(self.random_animations(True, time="2000", end="%d,%d" %(0,0), centery=centery  ))
        self.IMAGE_ANIMATIONS.extend(self.random_animations(False, time="2000", end="%d,%d" %(0,0), centery=centery  ))
        
        image_control=self.xbmc_window.getControl(image_control_id)
        
        
        #t = ffg_hangman(self.xbmc_window, self.title_control, factlet['name'] ) ; t.start()
        title=factlet['name']
        
        self.title_control.setText( title )
        self.title2_control.setText( factlet['p1'].replace(title+'  is a', 'A') )
        self.title3_control.setText( factlet['p2'].replace(title, 'It') )
        self.desc_control.setText( factlet['biology'].replace(title, 'It') )
        
        self.title_control.setAnimations( [('conditional', 'condition=true effect=fade    start=0    end=100    time=1000   tween=quadratic easing=out  delay=%s   ' %( 1.5*self.NEXT_IMAGE_TIME ) ), ]  )
        
        image=factlet['image']
#         #self.log(image)
#         images=factlet['images']
#         images_len=len(images )
#         #self.log( '   %d other images' % len(images ))
#         img_rand=random.randint(0, (images_len-1) )
#         
#         o1=self.xbmc_window.getControl(151)
#         o1.setImage(images[img_rand])
#         o1.setPosition(0, 600)
#         o1.setWidth(120)   
#         o1.setHeight(120)
#         o1.setAnimations( [ ('conditional', 'effect=fade  start=100      end=0        time=2000 tween=quadratic easing=in  delay=%s  condition=true' % (1.9*self.NEXT_IMAGE_TIME) ), ] )
#         o1.setVisible(True)        
        
        image_control.setVisible(False)
        image_control.setImage('')

        image_control.setImage(image)
        image_control.setPosition(end_x, end_y)
        image_control.setWidth(720)   
        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)
        # show the image
        image_control.setVisible(True)
        self.txt_group_control.setVisible(True)

    #def image_pump(self, ):

    def random_animations(self, animation_phase_in, time, end, centery, centerx=360):
        #centery is center-y of image on screen 
        #note start & end coords are relative to where image is on screen.
        if animation_phase_in:
            delay=0
        else:
            delay=(1.9*self.NEXT_IMAGE_TIME)
        
        fade_animation=    ('conditional', 'condition=true effect=fade    start=0    end=%s    time=%s   tween=quadratic easing=out  delay=0   ' %(100, (1*time) ) )
        fade_out_animation=('conditional', 'condition=true effect=fade    start=100  end=0     time=2000 tween=quadratic easing=in   delay=%s  ' % delay )
        flipy_animation   =('conditional', 'condition=true effect=rotatey start=0    end=180   time=%s   tween=circle    easing=out  delay=%s  center=%s,0 ' %(time, delay, centery) ),
                
        
        rotates=['rotatex', 'rotatey', 'rotate']
        zoom_starts=[0,500]
        pos_or_neg=['','-']
        
        
        rotate=random.choice(rotates)
        pn=random.choice(pos_or_neg)
        zs=random.choice(zoom_starts)
        
        direction=random.choice([1,0])
        up_down=random.choice([1,0])
        
        deg=random.randint(0,360)
        rad=math.radians(deg)
        sx = 720 * math.cos(rad)
        sy = 720 * math.sin(rad)
        start='%d,%d'%(sx,sy)
        #log('  %d - (%d,%d)' %(deg, sx,sy )   )
        
        if animation_phase_in:
            tweens=['circle','sine','back','elastic','bounce']
            tween=random.choice(tweens)    
            a=[
               [ #slide from anywhere
                fade_animation,
                ('conditional', 'condition=true effect=slide start=%s   end=%s    time=%s   tween=%s      easing=out delay=0   ' %(start, end,  time, tween) ),
               ],
               [ #drop from top
                fade_animation,
                ('conditional', 'condition=true effect=slide start=0,-720   end=%s    time=%s   tween=bounce  easing=out delay=0   ' %(       end,  time ) ),
               ],
               [ 
                fade_animation,
                ('conditional', 'condition=true effect=%s      start=%s%s    end=%s    time=%s   tween=circle  easing=out delay=%s  center=auto ' %( rotate, pn, (deg+deg),    0,  time, ( 0 ) ) ),
               ],
               [ #
                fade_animation,
                ('conditional', 'condition=true effect=zoom    start=%s    end=100    time=%s   tween=%s  easing=out delay=0  center=auto ' %(  zs ,time, tween) ),
               ],
               
            ]
        else:
            tweens=['circle','sine','back']
            tween=random.choice(tweens)    
            a=[
               [ #slide away
                fade_out_animation,
                ('conditional', 'condition=true effect=slide   start=%s   end=%s    time=%s   tween=%s      easing=in delay=%s   ' %( end,start,  time, tween, delay) ),
               ],
               [ #flip x disappear
                fade_out_animation,
                ('conditional', 'condition=true effect=rotatex start=0    end=%s90    time=%s   tween=circle  easing=in delay=%s center=%s,0  ' %( pn,        time, delay, centerx ) ),
               ],
               [ #random rotates
                fade_out_animation,
                ('conditional', 'condition=true effect=%s      start=0    end=%s%s    time=%s   tween=circle  easing=in delay=%s  center=auto ' %( rotate, pn, (deg+deg), time, delay ) ),
               ],
               [ #
                fade_out_animation,
                ('conditional', 'condition=true effect=zoom    start=100    end=%s    time=%s   tween=%s  easing=in delay=%s  center=auto ' %(  zs ,time, tween, delay) ),
               ],
               
            ]
            
        anim=random.choice(a)
        
        #b=a[3]
        if random.getrandbits(1):
            #log( '  flipped image'  )
            #b.extend(flipy_animation)
            anim.extend(flipy_animation)
        
        return anim

    def random_textcontrol_animations(self):
        delay=(1.9*self.NEXT_IMAGE_TIME)
        time=2000
        fade_animation=    ('conditional', 'condition=true effect=fade    start=0    end=100    time=%s   tween=quadratic easing=out  delay=0   ' %( (1*time) ) )
        fade_out_animation=('conditional', 'condition=true effect=fade    start=100  end=0      time=2000 tween=quadratic easing=in   delay=%s  ' % delay )

        a=[
           [ 
            fade_animation,
            fade_out_animation,
           ],
           ]
        
        return a[0]

class bggslide(ScreensaverBase):
    BACKGROUND_IMAGE = '' #'srr_blackbg.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 0
    SPEED = 0.7
    IMAGE_ANIMATIONS = []

    ID_STAT1_TXT=301
    ID_STAT2_TXT=302
    ID_STAT3_TXT=303
    ID_STAT4_TXT=304
    ID_STAT5_TXT=305
    ID_STAT6_TXT=306
    ID_STAT7_LIST=307
    ID_STAT8_LIST=308
    ID_STAT9_LIST=309
    ID_STAT10_LIST=310
    ID_RANK_TEXT=390
    image_control_ids=[102,103,104,105,106,107,108,109,110]
    MAIN_IMAGE_ID=101
    
    def load_settings(self):
        self.SPEED = 1.0
        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))
        self.MAX_TIME = int(30000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(120000.0 / self.SPEED)

    def init_xbmc_window(self):
        self.xbmc_window = ScreensaverXMLWindow( "slideshow03.xml", ADDON_PATH, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.setCoordinateResolution(5)
        self.xbmc_window.show()
    
    def stack_cycle_controls(self):
        self.txt_group_control=self.xbmc_window.getControl(200)
        self.title_control=self.xbmc_window.getControl(201)
        self.desc_control=self.xbmc_window.getControl(202)
        self.title2_control=self.xbmc_window.getControl(203)
        self.title3_control=self.xbmc_window.getControl(204)
        pass

    def start_loop(self):
        self.log('bgg screensaver start_loop')
        
        self.image_controls_cycle= cycle(self.image_control_ids)
        self.hide_loading_indicator()
        
        #pops the first one
        #factlet=self.facts_queue.get()
        
        while not self.exit_requested:
            #self.log('  using image: %s ' % ( repr(factlet) ) )
            #self.log( '  using:' + pprint.pformat(factlet, indent=1, depth=1) )

            try:
                if self.facts_queue.empty():
                    self.log('   queue empty '   )
                    #self.exit_requested=True
                    self.wait(5000)
                else:
                    #factlet=self.facts_queue.get()
                    factlet=self.facts_queue.get(block=True,timeout=5000)  #doesn't throw exception if empty!

                    #self.log( '  worker is alive:' + repr(self.worker_thread.isAlive()) )
                    self.log( '  using:' + pprint.pformat(factlet, indent=1, depth=1) )
                    

                    #pops an image control
                    image_control = self.image_controls_cycle.next()
                    
                    self.process_image(image_control, factlet)
                    
                    self.wait()  #waits for self.NEXT_IMAGE_TIME

            #if self.watchdog>=20:
            #    self.exit_requested=True
                    
            except Queue.Empty:
                self.log('   queue empty thrown')
                self.wait(5000)
                
            #self.preload_image(factlet['image'])
            
                
        self.log('start_loop end')

    
    def process_image(self, image_control_id, factlet ):

        self.fill_text_controls(factlet)
        
        t=self.MAX_TIME

        ctl_width=1280
        ctl_height=720
        
        SLIDES_TO_SHOW=6  
        CLUES_TO_SHOW=SLIDES_TO_SHOW-2  #+1 game title/desc  +1 game image
        
        TIME_PER_SLIDE=self.NEXT_IMAGE_TIME/SLIDES_TO_SHOW
        TIME_CLUE_SLIDES_DONE= TIME_PER_SLIDE * (CLUES_TO_SHOW)
        TIME_TITLE_SLIDE_DONE= TIME_CLUE_SLIDES_DONE + TIME_PER_SLIDE
        
        #log('  TIME_PER_SLIDE:%d  TIME_CLUE_SLIDES:%d'%(TIME_PER_SLIDE,TIME_CLUE_SLIDES))
            
        #self.IMAGE_ANIMATIONS=[]
        #self.IMAGE_ANIMATIONS.extend(self.random_animations( time="2000", end="%d,%d" %(0,0), centery=centery  ))
        #self.IMAGE_ANIMATIONS.extend(self.udlr_slide_animations( delay=0, time=SLIDE_TIME ) )
        
        #self.IMAGE_ANIMATIONS.extend( [ ('conditional', 'condition=true delay=0 time=2000 effect=slide start=1280,0 end=-1280,0 center=auto tween=cubic easing=out ' ),    ] )
        
        
        
        #self.IMAGE_ANIMATIONS.extend(self.random_animations(False, time="2000", end="%d,%d" %(0,0), centery=centery  ))

        
        ctl_game_tdesc=self.xbmc_window.getControl(200)  #the width of this control is 800
        ctl_game_stats=self.xbmc_window.getControl(300)  #the width of this control is 800
        

        ctl_game_stats.setVisible(False)
        ctl_game_stats.setPosition(0, 0)
        
        ctl_game_stats.setAnimations(  self.fade_in_out_animation( 0, TIME_TITLE_SLIDE_DONE, 5000 ) +
                                      [self.animation_format(5000,  TIME_TITLE_SLIDE_DONE, 'slide', '580,0', '-800,0', 'linear', '' ), ]  )
        ctl_game_stats.setVisible(True)

        #ctl_game_tdesc.setAnimations( [ self.animation_format(TIME_CLUE_SLIDES_DONE, TIME_PER_SLIDE, 'fade',    0,      100, 'quadratic', '' ), ]  )
        ctl_game_tdesc.setAnimations( self.random_animations( (TIME_CLUE_SLIDES_DONE), TIME_PER_SLIDE)  )
        ctl_game_tdesc.setVisible(True)

        
        #log( 'no of images:' + repr(len(factlet.get('images'))) )
        
        if len(factlet.get('images')) < CLUES_TO_SHOW:
            CLUES_TO_SHOW=len(factlet.get('images'))
        #pick 5 random images 
        images=random.sample(factlet.get('images'), CLUES_TO_SHOW)
        #log( pprint.pformat(images) )
        
        

        for i, img in enumerate(images):
            iid=self.image_controls_cycle.next()
            img_ctl=self.xbmc_window.getControl( iid )
            img_ctl.setVisible(False)
            #log( '  TIME:%d id(%d) %d %s' %((TIME_PER_SLIDE*i),iid,i,pprint.pformat(img)) )
            img_ctl.setImage(img)
            
            img_ctl.setPosition(0, 0)
            img_ctl.setWidth(ctl_width)   
            img_ctl.setHeight(ctl_height)

            img_ctl.setAnimations( self.udlr_slide_animations( delay=(TIME_PER_SLIDE*i +(TIME_PER_SLIDE/2) ), time=TIME_PER_SLIDE ) )   #add a delay of half time per slide to give xbmc chance to load image
            #img_ctl.setAnimations( self.random_animations( (TIME_PER_SLIDE*i), TIME_PER_SLIDE ) )
            
            img_ctl.setVisible(True)
            

        #image=factlet.get('image')
        image_control=self.xbmc_window.getControl(self.MAIN_IMAGE_ID)
        
        image_control.setVisible(False)
        image_control.setImage('')
        image_control.setImage(factlet.get('image'))
        image_control.setPosition(0, 0)  
        image_control.setWidth(ctl_width)   
        image_control.setHeight(ctl_height)
        image_control.setAnimations( self.random_animations( TIME_TITLE_SLIDE_DONE, TIME_PER_SLIDE)  ) #  self.udlr_slide_animations( delay=0, time=SLIDE_TIME ) )
        image_control.setVisible(True)

        self.txt_group_control.setVisible(True)

    #def image_pump(self, ):
    def fill_text_controls(self, factlet):

    #id 200s
        title=factlet.get('name')
        self.title_control.setText( title )
        #self.title2_control.setText( factlet['p1'].replace(title+'  is a', 'A') )
        #self.title3_control.setText( factlet['p2'].replace(title, 'It') )
        self.desc_control.setText( factlet.get('description') )
        
        #self.title_control.setAnimations( [('conditional', 'condition=true effect=fade    start=0    end=100    time=1000   tween=quadratic easing=out  delay=%s   ' %( 1.5*self.NEXT_IMAGE_TIME ) ), ]  )

    #ids 300s
        stat1=self.xbmc_window.getControl(self.ID_RANK_TEXT)
        stat1.setLabel(factlet.get('rank_text'))
    
        stat1=self.xbmc_window.getControl(self.ID_STAT1_TXT)
        stat1.setLabel(factlet.get('players'))

        stat1=self.xbmc_window.getControl(self.ID_STAT2_TXT)
        stat1.setLabel(factlet.get('playtime'))
        
        stat1=self.xbmc_window.getControl(self.ID_STAT3_TXT)
        stat1.setLabel(factlet.get('min_age'))
        stat1=self.xbmc_window.getControl(self.ID_STAT4_TXT)
        stat1.setLabel(factlet.get('complexity'))

        stat1=self.xbmc_window.getControl(self.ID_STAT5_TXT)
        stat1.setLabel(factlet.get('year'))
        stat1=self.xbmc_window.getControl(self.ID_STAT6_TXT)
        stat1.setLabel(factlet.get('rating_average'))
        
        list1=self.xbmc_window.getControl(self.ID_STAT7_LIST)
        list1.reset()
        list1.addItems(factlet.get('categories'))
        
        list1=self.xbmc_window.getControl(self.ID_STAT8_LIST)
        list1.reset()
        list1.addItems(factlet.get('mechanics'))
        
        list1=self.xbmc_window.getControl(self.ID_STAT9_LIST)
        list1.reset()
        list1.addItems( factlet['designers'] + factlet['artists'])
        
        list1=self.xbmc_window.getControl(self.ID_STAT10_LIST)
        list1.reset()
        list1.addItems( factlet['families'])

        

    def udlr_slide_animations(self, delay, time):

        direction=random.choice([1,0])
        up_down=random.choice([1,0])
            
        #default dimension of the image control        
        ctl_width=1280
        ctl_height=720
        ctl_x=0

        if up_down:
            #with tall images, the image control dimension has to be tall 
            sx=0;ex=0
            sy=(-1*ctl_height) ;ey=720

        else:
            sx=1280;ex=(-1*ctl_width)
            sy=0;ey=0

        if direction:
            sx,ex=ex,sx
            sy,ey=ey,sy

        #fade_in_animation= ('conditional', 'condition=true delay={delay} time={time} effect=fade  start=0    end=100  tween=quadratic easing=out  '.format(delay=0,        time=2000) )
        #fade_out_animation=('conditional', 'condition=true delay={delay} time={time} effect=fade  start=100  end=0    tween=quadratic easing=in   '.format(delay=out_delay,time=2000) )
        
        #slide_animation= ('conditional', 'condition=true delay=0 time=%s effect=slide start=%d,%d end=%d,%d center=auto tween=cubic easing=out ' % ( self.MAX_TIME, sx,sy,ex,ey))    
        
        start='%d,%d'%(sx,sy)
        end='%d,%d'%(ex,ey)
        
        animation=[]
        #animation.extend( [fade_in_animation,fade_out_animation] )
        animation.extend( [self.animation_format(delay, time, 'slide', start, end, 'sine', 'out' ), ]   )
        #animation.extend( [self.animation_format(delay, time, 'slide', start, end, 'cubic', 'out' ), ]   )
        #animation.extend( [slide_animation, ]   )
        #log( pprint.pformat(animation) )
        return animation
        
    def fade_in_out_animation(self, start_delay, wait_time, fade_time=2000 ):
        out_delay=start_delay + wait_time - fade_time
        fade_in_animation= ('conditional', 'condition=true delay={delay} time={time} effect=fade  start=0    end=100  tween=quadratic easing=out  '.format(delay=start_delay, time=fade_time) )
        fade_out_animation=('conditional', 'condition=true delay={delay} time={time} effect=fade  start=100  end=0    tween=quadratic easing=in   '.format(delay=out_delay  , time=fade_time) )
        
        return [fade_in_animation,fade_out_animation]
        

    def random_animations(self, start_delay, wait_time, centery=0, centerx=360):
        #these animations are burst-wait-burst
        #centery is center-y of image on screen 
        #note start & end coords are relative to where image is on screen.

        time=2000   #animation time
        in_delay=start_delay
        out_delay=in_delay + wait_time - time
        
        
        #fade_in_animation= ('conditional', 'condition=true delay={delay} time={time} effect=fade  start=0    end=100  tween=quadratic easing=out  '.format(delay=in_delay, time=2000) )
        #fade_out_animation=('conditional', 'condition=true delay={delay} time={time} effect=fade  start=100  end=0    tween=quadratic easing=in   '.format(delay=out_delay,time=2000) )
        #flipy_animation   =('conditional', 'condition=true effect=rotatey start=0    end=180   time=%s   tween=circle    easing=out  delay=%s  center=%s,0 ' %(time, delay, centery) ),

        rotates=['rotatex', 'rotatey', 'rotate']
        zoom_starts=[0,500]
        pos_or_neg=['','-']
        
        rotate=random.choice(rotates)
        pn=random.choice(pos_or_neg)
        
        zs=random.choice(zoom_starts)
        
        direction=random.choice([1,0])
        up_down=random.choice([1,0])
        
        deg=random.randint(0,360)
        rad=math.radians(deg)
        sx = 720 * math.cos(rad)
        sy = 720 * math.sin(rad)
        start='%d,%d'%(sx,sy)
        end  ='%d,%d'%( 0, 0)
        #log('  %d - (%d,%d)' %(deg, sx,sy )   )

        rnd_deg='%s%s'%(pn,(deg+deg))
                
        in_tweens=['circle','sine','back','elastic','bounce']
        in_tween=random.choice(in_tweens)    

        out_tweens=['circle','sine','back']
        out_tween=random.choice(out_tweens)    

        phase_in_animations=[
           [ #slide from anywhere
            self.animation_format(in_delay, time, 'slide', start, end, in_tween, 'out' ),
           ],
           [ #drop from top
            self.animation_format(in_delay, time, 'slide', '0,-720', 0, 'bounce', 'out' ),
           ],
           [ #rotates or spin
            self.animation_format(in_delay, time, rotate, rnd_deg, 0, 'circle', 'out', 'auto' ),
            #('conditional', 'condition=true delay=%s time=%s effect=%s      start=%s%s     end=%s       tween=circle  easing=out   center=auto ' %( in_delay, time, rotate, pn, (deg+deg),    0 ) ),
           ],
           [ #zoom from very big or very small
            self.animation_format(in_delay, time, 'zoom', zs, 100, in_tween, 'out', 'auto' ),
            #('conditional', 'condition=true delay=%s time=%s effect=zoom    start=%s       end=100      tween=%s      easing=out   center=auto ' %(  in_delay, time, zs , in_tween) ),
           ],
           
        ]

        phase_out_animations=[
           [ #slide away
            self.animation_format(out_delay, time, 'slide', end, start, out_tween, 'in' ),
            #('conditional', 'condition=true delay=%s time=%s effect=slide   start=%s   end=%s        tween=%s      easing=in    ' %( out_delay, time, end,start,   out_tween) ),
           ],
           [ #flip horizontal. the random.choice(360/720) is for the center.  makes the image either fall front/back or flip front/back
            self.animation_format(out_delay, time, 'rotatex', 0, '%s90'%pn, 'circle', 'in', '%s,0'%(random.choice([360,720])) ), #center x needs to be in the
            #('conditional', 'condition=true delay=%s time=%s effect=rotatex start=0    end=%s90      tween=circle  easing=in  center=%s,0  ' %( out_delay, time, pn,          centerx ) ),
           ],
           [ #random rotates
            self.animation_format(out_delay, time, rotate, 0, rnd_deg, 'circle', 'in', 'auto' ),
            #('conditional', 'condition=true delay=%s time=%s effect=%s      start=0    end=%s%s      tween=circle  easing=in  center=auto ' %( out_delay, time, rotate, pn, (deg+deg)  ) ),
           ],
           [ #
            self.animation_format(out_delay, time, 'zoom', 100, zs, out_tween, 'in', 'auto' ),
            #('conditional', 'condition=true delay=%s time=%s effect=zoom    start=100    end=%s      tween=%s  easing=in  center=auto ' %( out_delay, time, zs , out_tween ) ),
           ],
           
        ]

        animation=[]
        #animation.extend( [fade_in_animation,fade_out_animation] )
        animation.extend( self.fade_in_out_animation(in_delay, wait_time, time) )
        
        
        animation.extend( random.choice(phase_in_animations) )
        #animation.extend( phase_in_animations[2] )
        animation.extend( random.choice(phase_out_animations) )
        #animation.extend( phase_out_animations[1] )
        
        #b=a[3]
        #if random.getrandbits(1):
            #log( '  flipped image'  )
            #b.extend(flipy_animation)
        #    anim.extend(flipy_animation)
        
        return animation

    def animation_format(self, delay, time, effect, start, end, tween='', easing='', center='', extras=''  ):
        a='condition=true delay={0} time={1} '.format(delay, time) 
            
        a+= 'effect={} '.format(effect)
        a+= 'start={} '.format(start)
        a+= 'end={} '.format(end)
        
        if center: a+= 'center={} '.format(center)
        if tween:  a+= 'tween={} '.format(tween)
        if easing: a+= 'easing={} '.format(easing)  #'in' 'out'
        if extras: a+= extras  
        
        #log( '  ' + a ) 
        return ('conditional', a )

    def random_textcontrol_animations(self):
        delay=(1.9*self.NEXT_IMAGE_TIME)
        time=2000
        fade_animation=    ('conditional', 'condition=true effect=fade    start=0    end=100    time=%s   tween=quadratic easing=out  delay=0   ' %( (1*time) ) )
        fade_out_animation=('conditional', 'condition=true effect=fade    start=100  end=0      time=2000 tween=quadratic easing=in   delay=%s  ' % delay )

        a=[
           [ 
            fade_animation,
            fade_out_animation,
           ],
           ]
        
        return a[0]

class HorizontalSlideScreensaver2(ScreensaverBase):
    BACKGROUND_IMAGE = 'srr_blackbg.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 0
    DISTANCE_RATIO = 0.7
    SPEED = 1.0
    CONCURRENCY = 1.0
    #SCREEN = 0

    def load_settings(self):
        self.SPEED = 1.0
        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))
        self.MAX_TIME = int(30000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(6000.0 / self.SPEED)
        
    def stack_cycle_controls(self):
#         for txt_ctl, img_ctl in self.tni_controls:
#             self.xbmc_window.addControl(img_ctl)
# 
#         self.txt_background=ControlImage(720, 0, 560, 720, 'srr_dialog-bg.png', aspectRatio=1)
#         self.xbmc_window.addControl( self.txt_background  )
#         
#         for txt_ctl, img_ctl in self.tni_controls:
#             self.xbmc_window.addControl(txt_ctl)
        pass                        

    def process_image(self, image_control, factlet ):

        MOVE_ANIMATION = (
            'effect=slide start=1280,0 end=-1280,0 center=auto time=%s '
            'tween=circle easing=out delay=0 condition=true'
        )

        FADE_ANIMATION = (
            'effect=fade delay=10 time=4000 '
            'tween=linear easing=out condition=true'
        )
        
        #image_control=tni_control[1]
        #text_control=tni_control[0]
        image=factlet['image']
        
        image_control.setVisible(False)
        image_control.setImage('')
        #text_control.setVisible(False)
        #text_control.setText('')
        
        self.txt_background.setVisible(False)  
        self.txt_background.setImage('')

        time = self.MAX_TIME #/ zoom * self.DISTANCE_RATIO * 100   #30000

        animations = [
            ('conditional', MOVE_ANIMATION % time)
        ]
        # set all parameters and properties

        image_control.setImage(image)
        image_control.setPosition(0, 0)
        image_control.setWidth(1280)   #16:9
        #image_control.setWidth(1680)    #21:9  
        image_control.setHeight(720)
        image_control.setAnimations(animations)
        # show the image
        image_control.setVisible(True)


#         c=self.xbmc_window.getControl(101)
#         #log('    **' +c.getText() )
#         c.setText( desc_and_image[0] )
#         cy=c.getY()
#         #c.setPosition( 0, cy+10 )
#         self.xbmc_window.removeControl(c)   #graaaahhhh!!! won't work. access violation!
#         self.xbmc_window.addControl(c)


        self.txt_background.setImage('srr_dlg-bg.png')
        #self.txt_background.setPosition(0, 0)
        # re-stack it (to be on top)
        #self.xbmc_window.removeControl(self.txt_background)
        #self.xbmc_window.addControl(self.txt_background)
        #self.txt_background.setColorDiffuse('0xCCCCCCCC') 
        self.txt_background.setVisible(True)  

    
def cycle(iterable):
    saved = []
    for element in iterable:
        yield element
        saved.append(element)
    while saved:
        for element in saved:
            yield element

if __name__ == '__main__':
    pass
