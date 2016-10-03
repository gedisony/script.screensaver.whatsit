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
import sys

import requests
import resources.lib.requests_cache 

import bs4
import pickle  
import re

import xbmc


from screensaver import addon, ADDON_PATH, SQLITE_FILE, BGG_INDEX_FILE, PKMON_INDEX_FILE
from screensaver import log, localize
import pprint

REQ_TIMEOUT=3  #requests timeout in seconds


gen1        = addon.getSetting("gen1") == "true"
gen2        = addon.getSetting("gen2") == "true"
gen3        = addon.getSetting("gen3") == "true"
gen4        = addon.getSetting("gen4") == "true"
gen5        = addon.getSetting("gen5") == "true"
gen6        = addon.getSetting("gen6") == "true"
gen7        = addon.getSetting("gen7") == "true"

def db_connect(db_file=SQLITE_FILE):
    try:
        from pysqlite2 import dbapi2 as sqlite
    except:
        from sqlite3 import dbapi2 as sqlite             
 
    return sqlite.connect(SQLITE_FILE)
    #return conn.cursor()


def generate_random_poke_id():
    while True:        
        data = make_poke_range_list()
        random.shuffle(data)
        for i in data:
            yield i 

def make_poke_range_list():
    #gen 1 =   1-151
    #gen 2 = 152-251
    #gen 3 = 252-386
    #gen 4 = 387-493
    #gen 5 = 494-649
    #gen 6 = 650-721
    
    ids=[]
    
    if gen1:
        ids.extend(range(1,151))
    if gen2:
        ids.extend(range(152,251))
    if gen3:
        ids.extend(range(252,386))
    if gen4:
        ids.extend(range(387,493))
    if gen5:
        ids.extend(range(494,649))
    if gen6:
        ids.extend(range(650,721))
    
    #ids=[];ids.extend(range(1,8))
    
    return ids        


class factsBase(object):
    def __init__(self):
        self.load_settings()
    
    def load_settings(self):
        pass
    
    def generate_random_slide(self):
        pass

    def remove_parens(self, string_with_parens):
        regex = re.compile(".*?\((.*?)\)")
        return re.sub(r'\([^)]*\)', '', string_with_parens)  #re.findall(regex, string_with_parens)[0]        

class boardgamegeek(factsBase):

    data=[]
    data_file=BGG_INDEX_FILE
    
    
    

    def load_settings(self):
        self.use_bgg_rank=addon.getSetting("use_bgg_rank") == "true"
        

        pass

    def load_data(self):
        #self.use_bgg_rank=True
        if self.use_bgg_rank:
            self.data=[]
            self.data=load_dict( self.data_file )
            log('  index file loaded: %d items' % len(self.data))
        else:
            #load hotness list
            self.get_hotness_list(60) 
            log('  hotness list downloaded: %d items' % len(self.data))
            
    
    def generate_index_from_web(self, progress_function ):
        start_page=1
        end_page=7
        log( 'Downloading boardgame list %d-%d' %(start_page, end_page-1) )
        for i in range(start_page,end_page):
            page = self.get_game_list(i)
            xbmc.sleep(1000)
            progress_function(localize(32307) %(i,end_page-1))
            xbmc.sleep(1000)
            
            self.data.extend(page)
        
        #log( pprint.pformat(self.data, indent=1) )
        
        save_dict( self.data, self.data_file )
        log('    created bgg index file(%s) %d items' %(self.data_file, len(self.data) )   )        

    def get_hotness_list(self,num_items):
        self.data=[]
        
        r = requests.get('https://api.geekdo.com/api/hotness?domain=boardgame&nosession=1&objecttype=thing&showcount=%s' %num_items, timeout=REQ_TIMEOUT )
        log( '  hotness list cached:%s' %(repr(r.from_cache )) )
        
        j = r.json()  
        #log( pprint.pformat(j) )
        
        items=j.get('items')
        
        for idx,i in enumerate(items,1):
            game_id=i.get('objectid')
            game_name=i.get('name')
            hotness_info='Hotness rank #{0}'.format( idx )
            
            self.data.append( {'id':game_id, 'name':game_name, 'urlname':i.get('href'),'rank_text':hotness_info } )
        pass

    def get_game_list(self,page_no):
        
        #this json returns hotness list
        #https://api.geekdo.com/api/hotness?domain=boardgame&nosession=1&objecttype=thing&showcount=30
        
        #these queries are used to filter by category / mechanic
        #https://boardgamegeek.com/geekitem.php?instanceid=5&objecttype=property&objectid=2023&subtype=boardgamemechanic&pageid=1&sort=rank&view=boardgames&modulename=linkeditems&callback=&showcount=10&filters[categoryfilter]=&filters[mechanicfilter]=&action=linkeditems&ajax=1
        #https://boardgamegeek.com/geekitem.php?instanceid=5&objecttype=property&objectid=1009&subtype=boardgamecategory&pageid=1&sort=rank&view=boardgames&modulename=linkeditems&callback=&showcount=10&filters[categoryfilter]=&filters[mechanicfilter]=&action=linkeditems&ajax=1        
        
        page = requests.get('https://boardgamegeek.com/browse/boardgame/page/%s' %page_no, timeout=REQ_TIMEOUT )
        log( '  page %d cached:%s ' %(page_no, repr(page.from_cache )) )
        #log(  repr( page.text ) )
        game_id=''
        page_data=[]
        soup = bs4.BeautifulSoup(page.text)
        
        #tr=soup.findAll("tr", {"id":"row_"} )
        td=soup.select('table.collection_table tr[id="row_"] td.collection_objectname. a' )
        
        rank_td=soup.select('table.collection_table tr[id="row_"] td.collection_rank' )
        #log( repr( rank_td ))
        #log( repr( td ))
        
        if len(rank_td)==len(td):
            #iterating through 2 lists!
            for r, a in zip(rank_td, td):
                #log( 'zzz ' + repr(a.get('href')) + ' ' + a.get('href').split('/')[2] )
                if a.get('href'):
                    game_id=a.get('href').split('/')[2]
                    game_name=a.text
                    game_rank='Boardgame rank #{0}'.format(r.text.strip())
                    #log('#{0:>3} {1} {2}'.format(game_rank.strip(), game_id, game_name ) )
                    page_data.append( {'id':game_id, 'name':game_name, 'urlname':a.get('href'),'rank_text':game_rank, } )
        else:
            for a in td:
                #log( repr( a.text ))
                #log( repr(a.get('href')) + ' ' + a.get('href').split('/')[2] )
                if a.get('href'):
                    game_id=a.get('href').split('/')[2]
                    #url_name=a.get('href').split('/')[3]
                    game_name=a.text
                    game_rank=''
                    page_data.append( {'id':game_id, 'name':game_name, 'urlname':a.get('href'), } )

        return page_data
        

    def get_bg_categories(self):
        #i used this code to generate strings.po for game categories
        #page = requests.get('https://boardgamegeek.com/browse/boardgamecategory' )
        page = requests.get('https://boardgamegeek.com/browse/boardgamemechanic', timeout=REQ_TIMEOUT )
        
        soup = bs4.BeautifulSoup(page.text)
        
        s=''
        po_id=''
        category_id=''
        
        td=soup.select('table.forum_table a' )
        #log( repr( td ))
        for idx, a in enumerate(td):
            #log( 'msgctxt "#324%.2d"\nmsgid "%s"\nmsgstr ""\n\n'  % (idx+1, a.text ))
            #log( repr(a.get('href')) + ' ' + a.get('href').split('/')[2] )
            
            category_id=a.get('href').split('/')[2]
            
            s=s+'msgctxt "#325%.2d"\nmsgid "%s (%s)"\nmsgstr ""\n\n'  % (idx+1, a.text, category_id )
            
            po_id=po_id+'325%.2d|' % (idx+1)

        log( s )
        log( po_id )
        
    def generate_random_slide(self):
        
        p=random.randint(1, len(self.data) )
        #p=self.id_generator.next()
        #p=718
        
        #game_id=self.data[p]['id']
        #log( '  getting info for %s %s' %(game_id, self.data[p]['name'] ) )
        #game_id='28023'
        return self.get_bgg_game(p)

    def get_bgg_game(self,data_index):
        game_id=self.data[data_index]['id']
        #game_id=187056
        game_name=self.data[data_index]['name']
        log( '  getting info for (%s) %s' %(game_id, game_name ) )
        
        from resources.lib.boardgamegeek import BoardGameGeek
        bgg= BoardGameGeek()

        g = bgg.game(game_id=game_id)
#         log( 'alternative_names:'+repr( g.alternative_names))
#         log( 'thumbnail:'+repr( g.thumbnail))
#         log( 'image:'+repr( g.image))
#         log( 'description:'+repr( g.description))
#         log( 'families:'+repr( g.families))
#         log( 'categories:'+repr( g.categories))
#         log( 'mechanics:'+repr( g.mechanics))
#         log( 'expansions:'+repr( g.expansions))
#         log( 'expands:'+repr( g.expands))
#         log( 'implementations:'+repr( g.implementations))
#         log( 'designers:'+repr( g.designers))
#         log( 'artists:'+repr( g.artists))
#         log( 'publishers:'+repr( g.publishers))
#         log( 'expansion:'+repr( g.expansion))
#         log( 'year:'+repr( g.year))
#         log( 'min_players:'+repr( g.min_players))
#         log( 'max_players:'+repr( g.max_players))
#         log( 'playing_time:'+repr( g.playing_time))
#         log( 'min_age:'+repr( g.min_age))
#         log( 'users_rated:'+repr( g.users_rated))
#         log( 'rating_average:'+repr( g.rating_average))
#         log( 'rating_bayes_average:'+repr( g.rating_bayes_average))
#         log( 'rating_stddev:'+repr( g.rating_stddev))
#         log( 'rating_median:'+repr( g.rating_median))
#         log( 'users_owned:'+repr( g.users_owned))
#         log( 'users_trading:'+repr( g.users_trading))
#         log( 'users_wanting:'+repr( g.users_wanting))
#         log( 'users_wishing:'+repr( g.users_wishing))
#         log( 'users_commented:'+repr( g.users_commented))
#         log( 'rating_num_weights:'+repr( g.rating_num_weights))
#         log( 'rating_average_weight:'+repr( g.rating_average_weight))
#         log( 'ranks:'+repr( g.ranks))        
        
        self.data[data_index].update({"factlet_type": self.__class__.__name__,
                                      "image"      :g.image, 
                                      "thumbnail"  :g.thumbnail, 
                                      "description":g.description, 
                                      #"families"   :g.families,      #not useful 
                                      "categories" :g.categories, 
                                      "mechanics"  :g.mechanics, 
                                      "designers"  :g.designers,
                                      "artists"    :g.artists,
                                      "publishers" :g.publishers,
                                      "year"       :'%s' %g.year,
                                      "players"    :'%d-%d' %(g.min_players,g.max_players),
                                      "playtime"   :'%s Min(s)' %g.playing_time,
                                      "min_age"    :'%s+' % g.min_age,
                                      "rating_average":'%.2f' %g.rating_average,
                                      "complexity" :'%.2f/5'%g.rating_average_weight,
                                      }  )
              
        self.data[data_index].update({
                                      "images" : self.get_game_images(game_id)
                                      }  )
          
        return self.data[data_index]

    def get_game_images(self, game_id):
        #JSON
        #https://api.geekdo.com/api/images?ajax=1&date=alltime&gallery=all&nosession=1&objectid=187056&objecttype=thing&pageid=1&showcount=36&size=thumb&sort=hot&tag=
        images=self.get_game_images_filtered(game_id=game_id,
                             image_size='medium',  #thumb large
                             gallery='all',       # ["all","game","people","creative",]
                             tags='components'     #can comma separate, AKA categories = ["","BoxFront","BoxBack","Components","Customized","Play","Miscellaneous","Mature","uncat"]
                             )
        
        #log('    {} images'.format(len(images)) )
        
        if len(images) < 10:
            #get more images without game+components filter
            images.extend( self.get_game_images_filtered(game_id=game_id,
                                 image_size='medium',  #thumb large
                                 gallery='all',        # ["all","game","people","creative",]
                                 tags=''               #can comma separate, AKA categories = ["","BoxFront","BoxBack","Components","Customized","Play","Miscellaneous","Mature","uncat"]
                                 )
                          )
        #log( pprint.pformat(images) ) 
        return images 
        
    def get_game_images_filtered(self, game_id, image_size, gallery, tags):
        request_url_template='https://api.geekdo.com/api/images?ajax=1&date=alltime&gallery={3}&nosession=1&objectid={0}&objecttype=thing&pageid=1&showcount=48&size={1}&sort=hot&tag={2}'
        request_url=request_url_template.format(game_id,image_size,tags,gallery)

        images=[]
        
        r = requests.get( request_url, timeout=REQ_TIMEOUT )
        log('  get game images cached:{0!r} {1}'.format(r.from_cache, request_url))
        
        j = r.json()  #log( pprint.pformat(j) )
        imgs=j.get('images')

        #for img in imgs:
        #    log( img.get('caption') + ' ' + img.get('imageurl') + ' ' + img.get('imageurl_lg'))
        
        if imgs:
            images = [ 'http:' + img.get('imageurl') for img in imgs ]
        else:
            images=[]
        
        return images

class bulbgarden(factsBase):
    list='http://bulbapedia.bulbagarden.net/wiki/Category:Generation_I_Pok%C3%A9mon'
    
    data=[]
    data_file=PKMON_INDEX_FILE
    id_generator=generate_random_poke_id() #use a generator to guarantee a non repeating id

    def load_settings(self):
        #self.load_data()
        pass
    
    def generate_index_from_db(self):
        #build the sqlite file from https://github.com/veekun/pokedex
        #the sqlite file is 50mb, it is not included in the addon
                 
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        c=db_connect()
        c.row_factory = dict_factory
        cc = c.cursor()
        
        cc.execute('SELECT p.generation_id as generation, p.id,g.name, g.genus, sh.name as shape, '\
                    '(SELECT group_concat( t.identifier) FROM pokemon_types AS pt INNER JOIN types AS t ON  pt.type_id=t.id  WHERE pt.pokemon_id=p.id  ) AS type '\
                    '  FROM pokemon_species AS p '\
                    '  INNER JOIN pokemon_species_names AS g ON p.id=g.pokemon_species_id '\
                    '  INNER JOIN pokemon_shape_prose AS sh ON sh.pokemon_shape_id=p.shape_id '\
                    ' WHERE g.local_language_id=9 AND sh.local_language_id=9 ORDER BY p.id ' )
                    
        rows = cc.fetchall()       
        
        for row in rows:
            log('    ' + repr( row )  ) 
        
        cc.close
        
        save_dict( rows, self.data_file )
        log('    created pokemon index file(%s)' %(self.data_file )   )
            
        return rows

    def load_data(self):
        self.data = load_dict( self.data_file )
        self.data.insert(0,None)  #move the first entry so that our index corresponds to the pokemon id. 
        #log('    vvvsss' + repr(self.data[7]))

    def get_bulbapedia_entry(self, pokemon_id):
        counter=0
        pokemon_name=self.data[pokemon_id].get('name')
        url='http://bulbapedia.bulbagarden.net/wiki/{0}_(Pok%C3%A9mon)'.format( pokemon_name )
        #log(  repr( url ) )
        
#         if self.data[pokemon_id].has_key('image'):
#             #no need to requery the site of we already have info.
#             log( '  already have info for #%.3d %s' %(pokemon_id, pokemon_name ) )
#             return self.data[pokemon_id]
#         else:
        log( '  getting info for #%.3d %s' %(pokemon_id, pokemon_name ) )
        
        image=''
        
        page = requests.get(url, timeout=REQ_TIMEOUT)
        log( '    cached:' + repr(page.from_cache ) )
        
        soup = bs4.BeautifulSoup(page.text)    
        #log(  repr( page.text ) )
        
        #right_table=soup.findAll("srcset")
        #log( '**%s' %( right_table ))
        
        div = soup.find("div", {"id": "mw-content-text"})   #log( '%s' %( div ))
        table=div.findAll("table")[7]     #log( '%s' %( table ))
        a = table.find("a")   #log( '%s' %( a ))
        
        #covers = soup.select('table.roundy a.image img[srcset]')
        #for c in covers:
        #    log( '##%s' %( c ))
        
        
        sanitized_pokemon_name=pokemon_name.replace('.','\.')                 #for css class selector
        sanitized_pokemon_name=sanitized_pokemon_name.replace(' ','.')
        
        #log( '**sanitized_pokemon_name:%s' %(  sanitized_pokemon_name  ))
        

        if '.' in sanitized_pokemon_name:
            #this is not as accurate but i could not match Mr. Mime 
            #img_a=soup.select('table.roundy a.image img[alt="Mr\..Mime"]'  )
            img_a=soup.select('table.roundy a.image img[srcset$="2x"]'  )
        else:
            img_a=soup.select('table.roundy a.image img[alt*="%s"]' %sanitized_pokemon_name )
        
        #log( '***%s' %(  img_a  ))
        
        if img_a:
            img= img_a[0] 
            #log('  __' + repr(      img["srcset"]                ) )
            srcsets = img["srcset"].replace(' ',',').split(',')   # srcset="http://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/375px-001Bulbasaur.png 1.5x, http://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/500px-001Bulbasaur.png 2x"
            image = srcsets[-2]
            
            #img_src=img["src"]       #log('  __' + repr(     img_src         ) )
            #image=img_src.replace('/250px-', '/500px-')  #can't guarantee a 500px version. we just use the srcset method above
            #image=img_src
            #log('  image  :' +       image        )
            

        #get bulbgarden archives link for other images:
        archives_links=soup.select('div a[href*="archives"]'  )
        #archives_link=soup.select('div a[title*="%s"]' %pokemon_name )
        #log('  archives_link' + repr( archives_link ))
        #for ar in archives_links:
            #log('  ar' + repr( ar ))
        
        if archives_links:
            ar_image_url=archives_links[1]['href']   #0,1&2 is probably the same

        archive_images=self.get_archive_images(ar_image_url)
        
        #log('  ar_image_url:' + repr( ar_image_url ))

        bio=div.findAll("p")    
        #log('  all<p>' + repr(     bio.text       ) )
        p1=bio[0].text  #Nidoqueen  is a dual-type Poison/Ground Pokémon.
        p2=bio[1].text  #It evolves from Nidorina when exposed to a Moon Stone. It is the final form of Nidoran.
        p1=self.remove_parens(p1)
        #log('  p1&2' + p1 +' ' + p2 )
        
#         for section in div.findAll('h2'):
#             log( repr( section ))
#             log( repr( section.findNextSibling(text=None) ))
#             
#             nextNode = section
#             while True:
#                 nextNode = nextNode.nextSibling
#                 try:
#                     tag_name = nextNode.name
#                 except AttributeError:
#                     tag_name = ""
#                 if tag_name == "p":
#                     log( repr( nextNode.string ))
#                 else:
#                     log( '********')
#                     break
 
 
#         h2=soup.select('h2 span[id="Biology"]')[0]
#         log( repr( h2 ))
#         log( '  '+ h2['id'] )

        #get short biology info        
        #search for the next <p> after id="biology"
        h2=div.find(name='span', attrs={"id":"Biology"} )

        #log( repr( h2 ))
        #log( repr( h2.parent ))
        #log( repr( h2.parent.findNextSibling(text=None) ))
        
        ns=h2.parent
        
        while counter < 10:
            counter+=1
            #log('  ns name:' + ns.name )
            if ns.name == 'p':
                break
            else:
                ns=ns.findNextSibling(text=None)
        
        #log('  ns text:' + ns.text )
        
        biology_desc=ns.text
        #log('  biology:' + repr(biology_desc) )

        self.data[pokemon_id].update({
                                      "factlet_type": self.__class__.__name__,
                                      "image":image, 
                                      "biology": biology_desc, 
                                      "p1":p1, 
                                      "p2":p2, 
                                      "images": archive_images 
                                      }  )
        #log('    '+ repr(self.data[pokemon_id] ))
        
        return self.data[pokemon_id]

    def get_archive_images(self, archives_url):
        
        return None  #skip archive images for now
        #log( '    getting archive images %s' %(archives_url ) )
        images=[]
        page = requests.get(archives_url, timeout=REQ_TIMEOUT)
        soup = bs4.BeautifulSoup(page.text)    

        a_imgs = soup.select('li.gallerybox div.thumb a.image img')
        
        #log('  a_imgs:' + repr( a_imgs ))
        count = 0
        for ar in a_imgs:
            #log('  img:' + repr( ar ))
            if ar.get('srcset'):
                #srcsets = img["srcset"].replace(' ',',').split(',')   # srcset="http://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/375px-001Bulbasaur.png 1.5x, http://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/500px-001Bulbasaur.png 2x"
                #image = srcsets[-2]
                image=ar["srcset"].replace(' ',',').split(',')[-2]
            else:
                image=ar['src']
            #log('image:' + repr( image ))
            count = count+1    
            images.append(image)
            
            if count > 6:
                break
        
            
        #log( '      %d images' %(len(images) ) )
        return images
        
    def generate_random_slide(self):
        #p=random.randint(1, 151)
        p=self.id_generator.next()
        #p=718
        return self.get_bulbapedia_entry(p)
    
def save_dict( dict_to_save, pickle_filename ):
    with open(pickle_filename, 'wb') as output:
        pickle.dump(dict_to_save, output)
        output.close()

def load_dict( pickle_filename ):    
    with open(pickle_filename, 'rb') as inputpkl:
        rows_dict= pickle.load(inputpkl)
        inputpkl.close()    
    return rows_dict

if __name__ == '__main__':
    pass
