

from kivy.config import Config
# Config.set('input', 'mouse', 'mouse,disable_multitouch')
# Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
# Config.set('input', 'mouse', 'mouse,disable_on_activity')
# print(Config.get('input', 'mouse'))

import kivy
kivy.require('1.1.0')

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import App
from kivy.utils import platform
from kivy.properties import OptionProperty, ObjectProperty, StringProperty
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.bubble import Bubble
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window

import json

import logging
logging.basicConfig(level=logging.DEBUG)

from word2word import Word2word

import certifi
import os

# Here's all the magic !
os.environ['SSL_CERT_FILE'] = certifi.where()

Langs = ('en', 'fr', 'de', 'it', 'es', 'ru', 'zh_cn', 'zh_tw')
langNames = dict()
langNames['en'] = "English"
langNames['fr'] = "français"
langNames['de'] = "Deutch"
langNames['it'] = "italiano"
langNames['es'] = "español"
langNames['ru'] = "русский"
langNames['zh_cn'] = "简体中文"
langNames['zh_tw'] = "繁体中文"
promtTexts = dict()
promtTexts['en'] = "Enter word in text field"
promtTexts['fr'] = "Entrez un mot dans le champ de texte"
promtTexts['de'] = "Geben Sie das Wort in das Textfeld ein"
promtTexts['it'] = "Inserisci la parola nel campo di testo"
promtTexts['es'] = "Ingrese la palabra en el campo de texto"
promtTexts['ru'] = "Введите слово в текстовое поле"
promtTexts['zh_cn'] = "在文本字段中输入单词"
promtTexts['zh_tw'] = "在文本字段中輸入單詞"

windowWidth = Window.system_size[0]
windowHeight = Window.system_size[1]

class CopyTranslateBubble(Bubble):

    def __init__(self, translator, **kwargs):
        self.mode = 'normal'
        self.translator = translator
        super(CopyTranslateBubble, self).__init__(**kwargs)
        
    def do(self, action):
        print("do: ", action)
        if  action == 'Copy':
            print("Copy")
            Clipboard.copy(self.parent.text_selection)
        elif action == 'Translate':
            print("Translate", self.parent.text_selection)
            self.translator(self.parent.text_selection)
        self.hide()
        
    def hide(self):
        parent = self.parent
        if not parent:
            return
        parent.remove_widget(self)


class Translator(FloatLayout):
    '''Create a Translator that receives a custom widget from the kv lang file.

    Add an action to be called from the kv lang file.
    '''
    info = StringProperty()
    waitPopup = ObjectProperty()
    new_btn = ObjectProperty()
    trans_btn = ObjectProperty()
    out1_label = ObjectProperty()
    out2_label = ObjectProperty()
    text_box1 = ObjectProperty()
    text_box2 = ObjectProperty()
    dict_label = ObjectProperty()

    def __init__(self, datadir, **kwargs) :
        logging.info("MYLOGGING: %s", datadir)
        logging.warning("MYLOGGING: %s", datadir)
        self.datadir = datadir            
        self.dict = ''
        self.wx2wy = None
        self.wy2wx = None
        self.lang1 = ''
        self.lang2 = ''
        self.lang1Name = ''
        self.lang2Name = ''     
        self.text_selection = ''       
        self.waitPopup = Popup(title='', content=Label(
            text='Preparing the dictionary. Please wait a moment.'))
        self.configPopup = self.build_configPopup()

        super(Translator, self).__init__(**kwargs)
                
        self.text_box1.bind(text=self.text_action1)
        self.text_box2.bind(text=self.text_action2)
        self.text_box1.keyboard_mode = 'managed'
        self.text_box2.keyboard_mode = 'managed'
        self.text_box1.bind(focus=self.on_focus1)
        self.text_box2.bind(focus=self.on_focus2)

        self.text_box1.use_bubble = False 
        self.text_box2.use_bubble = False 
        self.text_box1.use_handles = False
        self.text_box2.use_handles = False
        self.text_box1.bind(on_touch_up=self.out1_touchup)
        self.text_box2.bind(on_touch_up=self.out2_touchup)
        self.textInput1 = ''
        self.textInput2 = ''
        
        self.copy_trans_bubble1 = CopyTranslateBubble(self.do_translate12)
        self.copy_trans_bubble2 = CopyTranslateBubble(self.do_translate21)
    
        Clock.schedule_once(self._load_settings, 0)
        

    def _load_settings(self, junk):
        try:
            with open(self.datadir + "/setting.txt") as fs:
                prevLangs = json.load(fs)
                print(prevLangs)
                self.lang1 = prevLangs[0]
                self.lang2 = prevLangs[1]
                self.set_dict("")
                fs.close()
        except FileNotFoundError:
            print(self.datadir + "/setting.txt not found")
            pass

    def build_configPopup(self) :
        configLayout = FloatLayout()
        self.spinner1 = Spinner(text='From', values=Langs,
                               size_hint=(None, None),
                               size=(150, 60),
                               pos_hint={'left': 0., 'top': 1.})
        trans_arrowLabel = Label(text=' <<-->> ',
                               size_hint=(None, None),
                               size=(80, 60),
                               pos_hint={'x': 0.17, 'top': 1.})
        self.spinner2 = Spinner(text='To', values=Langs,
                               size_hint=(None, None),
                               size=(150, 60),
                               pos_hint={'x': 0.27, 'top': 1.})
        setDictBtn = Button(text='Choose\nDictionary', size_hint=(.18, .1), 
                                 pos_hint={'x': 0.5, 'top': 1.})
        setDictBtn.bind(on_press=self.set_dict)
        cancelDictBtn = Button(text='Cancel', size_hint=(.15, .1), 
                                 pos_hint={'x': 0.7, 'top': 1.})
        cancelDictBtn.bind(on_press=self.cancel_dict)
        self.spinner1.bind(text=self.set_lang1)
        self.spinner2.bind(text=self.set_lang2)
        configLayout.add_widget(self.spinner1)
        configLayout.add_widget(trans_arrowLabel)
        configLayout.add_widget(self.spinner2)
        configLayout.add_widget(setDictBtn)
        configLayout.add_widget(cancelDictBtn)
        return Popup(title='', 
                     content=configLayout,
                     background_color = [1, 1, 0, 0.5])
        
    def set_lang1(self, obj, text) :
        # print("In set_lang1 ", text)
        self.lang1 = text
 
    def set_lang2(self, obj, text) :
        # print("In set_lang2", text)
        self.lang2 = text
        
    def do_config(self) :
        if self.lang1 in Langs:
            self.spinner1.text = self.lang1
        if self.lang2 in Langs:
            self.spinner2.text = self.lang2   
        self.configPopup.open()
        
    def set_dict(self, junk) :
        if self.lang1 not in Langs or self.lang2 not in Langs or self.lang1 == self.lang2 :
            return
        self.waitPopup.open()
        Clock.schedule_once(self._setdict, 0)
        
    def _setdict(self, junk) :
        text = self.lang1 + '-' + self.lang2
        if text != self.dict :
            self.reset_textboxes()
            print("Setting dict to: ", text)
            self.dict = text
            self.lang1Name = langNames[self.lang1]
            self.lang2Name = langNames[self.lang2]       
            self.wx2wy = Word2word(self.lang1, self.lang2, custom_savedir=self.datadir)
            print("x2y: ", self.wx2wy.compute_summary())
            # for word in self.wx2wy.word2x:
            #     print(word)
            self.n12 = int(self.wx2wy.compute_summary()['n_translations_per_word'])
            self.wy2wx = Word2word(self.lang2, self.lang1, custom_savedir=self.datadir)
            print("y2x: ", self.wy2wx.compute_summary())
            self.n21 = int(self.wy2wx.compute_summary()['n_translations_per_word'])
            self.text_box1.text_language = self.lang1
            self.text_box2.text_language = self.lang2
            if self.lang1 in ('zh_cn', 'zh_tw'):
                # self.text_box1.hint_text = u"测试 prédire"
                self.text_box1.font_name = "DroidSansFallback"
                self.out1_label.font_name = "DroidSansFallback"
            else:
                self.text_box1.font_name = "Roboto"
                self.out1_label.font_name = "Roboto"
                
            if self.lang2 in ('zh_cn', 'zh_tw'):
                # self.text_box2.hint_text = u"测试 prédire"
                self.text_box2.font_name = "DroidSansFallback"
                self.out2_label.font_name = "DroidSansFallback"
            else:
                self.text_box2.font_name = "Roboto"
                self.out2_label.font_name = "Roboto"

            self.out1_label.text = self.lang1Name + ": "
            self.out2_label.text = self.lang2Name + ": "
            
            # self.text_box1.text = promtTexts[self.lang1]
            # self.text_box2.text = promtTexts[self.lang2]
            # self.dict_label.text = self.lang1 + " <<==>> " + self.lang2
            self.dict_label.text = 'Enter single word'
            with open(self.datadir + "/setting.txt", 'w+') as fso:
                json.dump([self.lang1, self.lang2], fso)

            self.configPopup.dismiss() 
        self.waitPopup.dismiss()
        
        self.copy_trans_bubble1.size[0] = min(350, 0.5*windowWidth)
        self.copy_trans_bubble2.size[0] = min(350, 0.5*windowWidth)
        
    def cancel_dict(self, junk) :
        self.configPopup.dismiss()
                
    # def on_touch_down(self, touch):
    #     print("Root touch down", touch)
    #     return True
        
    def on_focus1(self, instance, value):
        # print("on_focus1: ", value)
        if value:
            if self.text_box1.text != '' and self.text_box2.text != '':
                # print("hide keyboard 1")
                self.text_box1.hide_keyboard()
            elif self.text_box1.text == '' or self.text_box2.text == '':
                # print("show keyboard 1")
                self.text_box1.show_keyboard()
        else:
            self.text_box1.hide_keyboard()

    def on_focus2(self, instance, value):
        # print("on_focus2: ", value)
        if value:
            if self.text_box1.text != '' and self.text_box2.text != '':
                # print("hide keyboard 2")
                self.text_box2.hide_keyboard()
            elif self.text_box1.text == '' or self.text_box2.text == '':
                # print("show keyboard 2")
                self.text_box2.show_keyboard()
        else:
            self.text_box2.hide_keyboard()

    def reset_textboxes(self) :
        self.text_box1.text = ''
        self.text_box2.text = ''
        self.text_box1.focus = False
        self.text_box2.focus = False
        
    def text_action1(self, obj, text) :
        self.textInput1 = text
        print(obj, repr(text))
        # if len(self.textInput1)> 1 and text[-1] == '\n':
        #     self.do_translate()
            
    def text_action2(self, obj, text) :
        self.textInput2 = text
        print(repr(text))
        # if len(self.textInput2)> 1 and text[-1] == '\n':
        #     self.do_translate()
            
    def out1_touchup(self, obj, touch) :
        if self.text_box1.collide_point(touch.pos[0], touch.pos[1]):
            if len(self.text_box1.selection_text) > 0:
                self.text_selection = self.text_box1.selection_text.replace(',', '')
                # print("out1_doubletap", touch)
                if self.copy_trans_bubble1 not in self.children:
                    self.copy_trans_bubble1.pos[0] = touch.spos[0] * windowWidth - \
                        0.5 * self.copy_trans_bubble1.size[0]
                    self.copy_trans_bubble1.pos[1] = touch.spos[1] * windowHeight
                    self.add_widget(self.copy_trans_bubble1)
                    # self.text_box1.cancel_selection()
            else:
                if self.copy_trans_bubble1 in self.children:
                    self.remove_widget(self.copy_trans_bubble1)
        return True

    def out2_touchup(self, obj, touch) :
        if self.text_box2.collide_point(touch.pos[0], touch.pos[1]):
            if len(self.text_box2.selection_text) > 0:
                self.text_selection = self.text_box2.selection_text.replace(',', '')
                # print("out2_doubletap", touch)
                if self.copy_trans_bubble2 not in self.children:
                    self.copy_trans_bubble2.pos[0] = touch.spos[0] * windowWidth - \
                        0.5 * self.copy_trans_bubble2.size[0]
                    self.copy_trans_bubble2.pos[1] = touch.spos[1] * windowHeight
                    self.add_widget(self.copy_trans_bubble2)
                    # self.text_box2.cancel_selection()
            else:
                if self.copy_trans_bubble2 in self.children:
                    self.remove_widget(self.copy_trans_bubble2)
        return True

    def do_translate(self) :
        if self.textInput1 != '' and self.textInput2 != '':
            print("do_translate neither text boxes empty", self.textInput1, self.textInput2)
            self.text_box1.text = ""
            self.text_box2.text = ""
        elif self.textInput1 != '':
            self.do_translate12(self.textInput1.strip())
        elif self.textInput2 != '':
            self.do_translate21(self.textInput2.strip())
        else:
            print("do_translate both text boxes empty")
            
    def do_translate12(self, word):
        if self.wx2wy == None :
            print("Please select a dict first")
            self.text_box2.text = "Please select a dict first"
            return 
        # print(getattr(self, 'user_data_dir'))
        if word == '':
            word = self.textInput1.strip()
        try:
            transText = self.wx2wy(word, n_best=self.n12)
            print(word, "->", transText)
            self.text_box1.text = word
            self.text_box2.text = ", ".join(transText)
        except KeyError as err:
            print("Error: {0}".format(err))
            self.text_box1.text = word
            self.text_box2.text = "no translation"        
        self.text_box1.cancel_selection()

    def do_translate21(self, word):
        if self.wy2wx == None :
            print("Please select a dict first")
            self.text_box2.text = "Please select a dict first"
            return 
        # print(getattr(self, 'user_data_dir'))
        if word == '':
            word = self.textInput2.strip()
        try:
            transText = self.wy2wx(word, n_best=self.n21)
            print(word, "->", transText)
            self.text_box1.text = ", ".join(transText)
            self.text_box2.text = word
        except KeyError as err:
            print("Error: {0}".format(err))
            self.text_box1.text = "no translation"
            self.text_box1.text = word
        self.text_box2.cancel_selection()


class TranslatorApp(App):

    def build(self):
        datadir = ''
        if platform == 'android':
            from android.storage import app_storage_path
            datadir = app_storage_path()
        else:
            datadir = getattr(self, 'user_data_dir')
        print(datadir)        
        
        return Translator(datadir, info='Translator')


if __name__ == '__main__':
    TranslatorApp().run()
