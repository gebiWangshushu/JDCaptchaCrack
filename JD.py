
#图像处理标准库
from PIL import Image   
#web测试 
from selenium import webdriver
#鼠标操作
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
#等待时间 产生随机数 
import time,random,datetime,os,shutil
import math
from functools import reduce
import operator


class ImageDownloader():

    def __init__(self, browser, min_images):
        self.browser = browser
        self.img_dir = "./images/jd/"
        self.classifier = ImageClassifier()
        self.min_images = min_images

    def download(self):
        """
        下载图片并分类合并
        """
        i = 0
        while i < self.min_images or self.classifier.need_to_merge > 0:
            print('{} need to merge'.format(self.classifier.need_to_merge))
            self.browser.find_element_by_class_name('JDJRV-img-refresh').click()
            img = self.get_images()
            folder = self.classifier.classify(img)
            class_folder = self.img_dir + str(folder) + '/'
            if not os.path.exists(class_folder):
                os.mkdir(class_folder)
            shutil.move(img.filename, class_folder)
            i += 1

    def get_images(self, find_this_img=""):
        """
        获取验证码图片
        :param find_this_img:
        :return:
        """
        time.sleep(0.3)
        img = self.browser.find_element_by_class_name('JDJRV-bigimg')
        location = img.location
        size = img.size
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']

        time.sleep(0.1)
        page_snap_obj = self.get_snap()
        image_obj = page_snap_obj.crop((left, top, right, bottom))

        # 图片相似才保存
        file_path = self.img_dir + str(time.time()) + '.png'
        if find_this_img != "":
            dog = Image.open(find_this_img)
            if self.compare2(dog, image_obj) < 0.6:
                image_obj.save(file_path)
        else:
            image_obj.save(file_path)
        return Image.open(file_path)

    def get_snap(self):
        """
        屏幕截图对象
        """
        self.browser.save_screenshot(self.img_dir + 'full_snap.png')
        page_snap_obj = Image.open(self.img_dir + 'full_snap.png')
        return page_snap_obj

    def compare2(self, image1, image2):
        """
        :图片相识度简单对比 图片越像返回值越趋近于0，返回 0-1 认为图片非常相似
        :param image1: 图片1对象
        :param image2: 图片2对象
        :return: 返回对比的结果
        """

        histogram1 = image1.histogram()
        histogram2 = image2.histogram()

        differ = math.sqrt(reduce(operator.add, list(map(lambda a,b: (a-b)**2,histogram1, histogram2)))/len(histogram1))
        return differ/100


class ImageClassifier():

    def __init__(self):
        self.image_merger = list()
        self.need_to_merge = 0

    def classify(self, img):
        """
        对图片进行分组
        :param img: 需要分组的图片
        :return: 图片被分配的组号
        """
        for merger in self.image_merger:
            if self.compare2(img, merger.base_img) < 1:
                if not merger.can_merge:
                    merger.update(img)
                    if merger.can_merge:
                        merger.merge()
                        self.need_to_merge -=1
                return self.image_merger.index(merger)

        merger = ImageMerger(img, len(self.image_merger))
        self.image_merger.append(merger)
        self.need_to_merge += 1
        return len(self.image_merger) - 1

    def compare2(self, image1, image2):
        """
        :图片相识度简单对比 图片越像返回值越趋近于0，返回 0-1 认为图片非常相似
        :param image1: 图片1对象
        :param image2: 图片2对象
        :return: 返回对比的结果
        """

        histogram1 = image1.histogram()
        histogram2 = image2.histogram()

        differ = math.sqrt(
            reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, histogram1, histogram2))) / len(
                histogram1))
        return differ / 100


class ImageMerger():

    def __init__(self, base_img, id):
        self.border_color_r = 120
        self.border_color_g = 120
        self.border_color_b = 120
        self.border_short_len = 6
        self.border_offset = 1
        self.border_bulb_height = 8
        self.border_square_height = 30
        self.down_dir = './images/merge/'

        self.id = id
        self.base_img = base_img
        border = self.find_border(base_img)
        self.down_top = border[1]
        self.up_bottom = border[0]
        self.top_img = base_img
        self.bottom_img = base_img
        self.can_merge = False

    def find_border(self, img):
        """
        获取滑块边界所在的y坐标
        """
        top = -1
        bottom = -1

        for y in range(img.size[1]):
            continuous = 0
            for x in range(self.border_offset, self.border_short_len + self.border_offset):
                pix = img.load()[x, y]
                if pix[0] == self.border_color_r and pix[1] == self.border_color_g and pix[2] == self.border_color_b:
                    continuous +=1
                    if continuous == self.border_short_len:
                        top = y - self.border_bulb_height
                        bottom = y + self.border_square_height
                        break
                else:
                    continuous = 0
            if top != -1:
                break
        return top, bottom

    def update(self, new_img):
        """
        更新当前分组图片的信息
        :param new_img: 用来更新当前分组的图片
        :return:
        """
        border = self.find_border(new_img)
        if border[0] > self.up_bottom:
            self.up_bottom = border[0]
            self.top_img = new_img
            print('id {} file {} update up_bottom {}'.format(self.id, new_img.filename, self.up_bottom))
        elif border[1] < self.down_top:
            self.down_top = border[1]
            self.bottom_img = new_img
            print('id {} file {} update down_top {}'.format(self.id, new_img.filename, self.down_top))
        self.can_merge = self.down_top < self.up_bottom

    def merge(self):
        """
        合并当前分组
        :return:
        """
        top = self.top_img
        bottom = self.bottom_img
        img_temp = top.crop((0, 0, top.width, self.up_bottom))
        # img_temp.show()
        bottom.paste(img_temp, (0, 0))
        bottom.save(self.down_dir + str(self.id) + '.png')


class JD(object):

    def __init__(self, step, is_headless, down_img_count, img_dir="./images/jd/"):
         #设置
        chrome_options = Options()
        # 无头模式启动
        if is_headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument("--start-maximized")
        # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--disable-gpu')
        # 设置屏幕器宽高
        chrome_options.add_argument("--window-size=1440,750")

        self.dr = webdriver.Chrome(executable_path=(r"./chromedriver_win32/chromedriver.exe"), chrome_options=chrome_options)
        self.dr.maximize_window()
        self.step = step
        self.img_dir = img_dir
        self.merge_dir = r"./images/merge/"
        self.down_img_count = down_img_count
        self.downloader = ImageDownloader(self.dr, down_img_count)

    def is_pixel_equal(self, img1, img2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        threshold = 60
        if (abs(pix1[0] - pix2[0] < threshold) and abs(pix1[1] - pix2[1] < threshold) and abs(
                pix1[2] - pix2[2] < threshold)):
            return True
        else:
            return False

    def get_gap(self, img1, img2):
        """
        获取缺口偏移量
        :param img1: 不带缺口图片
        :param img2: 带缺口图片
        :return:
        """
        left = 45
        for i in range(left, img1.size[0]):
            for j in range(img1.size[1]):
                if not self.is_pixel_equal(img1, img2, i, j):
                    left = i
                    return left
        return left

    def get_track7(self, distance):
        """
        根据偏移量和手动操作模拟计算移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        tracks = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 时间间隔
        t = 0.2
        # 初始速度
        v = 0

        while current < distance:
            if current < mid:
                a = random.uniform(2, 5)
            else:
                a = -(random.uniform(12.5, 13.5))
            v0 = v
            v = v0 + a * t
            x = v0 * t + 1 / 2 * a * t * t
            current += x

            if 0.6 < current - distance < 1:
                x = x - 0.53
                tracks.append(round(x, 2))

            elif 1 < current - distance < 1.5:
                x = x - 1.4
                tracks.append(round(x, 2))
            elif 1.5 < current - distance < 3:
                x = x - 1.8
                tracks.append(round(x, 2))

            else:
                tracks.append(round(x, 2))

        print(sum(tracks))
        return tracks

    def get_track(self, distance):
        track = []
        current = 0
        mid = distance * 7 / 8
        t = random.randint(2, 3) / 10
        v = 0
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        return track

    def autologin(self, url, username, password):
        """
        自动登录
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """     
        print('开始时间',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        self.dr.get(url)
        self.dr.implicitly_wait(4)

        lotab=self.dr.find_elements_by_class_name("login-tab-r")
        lotab[0].click()
        time.sleep(1)
        name=self.dr.find_element_by_id("loginname")
        name.send_keys(username)
        time.sleep(1)
        pwd=self.dr.find_element_by_id("nloginpwd")
        pwd.send_keys(password)
        time.sleep(1.3)
        logbtn=self.dr.find_element_by_id("loginsubmit")
        logbtn.click()

        if self.step == 1:
            self.downloader.download()
        elif self.step == 3:
            slide=self.dr.find_element_by_class_name("JDJRV-suspend-slide")
            if slide:
                print("已有素材,开始登录：")
                if slide:
                    for i in range(50):
                        self.do_login()
                        time.sleep(1.7)
                        title=self.dr.title
                        if title=="京东-欢迎登录":
                            continue
                        else:
                            print("登录成功："+title)
                            break
                else:
                    time.sleep(1.2)
                    logbtn.click()
        
        print('结束时间',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        pass
    
    def do_login(self):
        current_img = self.downloader.get_images()
        current_img.save(self.img_dir + 'current.png')
        files = os.listdir(self.merge_dir)
        simi_dict = dict()

        for f in files:
            temp_img = Image.open(self.merge_dir + f)
            simi_val = self.downloader.compare2(temp_img, current_img)
            simi_dict[f] = simi_val

        mini = min(simi_dict, key=simi_dict.get)
        image1 = Image.open(self.merge_dir + mini)
        gap = self.get_gap(image1, current_img)
        print(gap)

        # track = self.get_track7(gap + 20.85)
        # self.dragging(track)
        track = self.get_track(gap + 4)
        self.sliding(track)
        pass

    def sliding(self, track):
        button = self.dr.find_element_by_class_name('JDJRV-slide-btn')
        time.sleep(2)
        ActionChains(self.dr).click_and_hold(button).perform()
        time.sleep(0.2)
        # 根据轨迹拖拽圆球
        for track in track:
            ActionChains(self.dr).move_by_offset(xoffset=track, yoffset=0).perform()
        # 模拟人工滑动超过缺口位置返回至缺口的情况，数据来源于人工滑动轨迹，同时还加入了随机数，都是为了更贴近人工滑动轨迹
        imitate = ActionChains(self.dr).move_by_offset(xoffset=-1, yoffset=0)
        time.sleep(0.015)
        imitate.perform()
        time.sleep(random.randint(6, 10) / 10)
        imitate.perform()
        time.sleep(0.04)
        imitate.perform()
        time.sleep(0.012)
        imitate.perform()
        time.sleep(0.019)
        imitate.perform()
        time.sleep(0.033)
        ActionChains(self.dr).move_by_offset(xoffset=1, yoffset=0).perform()
        # 放开圆球
        ActionChains(self.dr).pause(random.randint(6, 14) / 10).release(button).perform()
        time.sleep(random.random() * 5 + 0.5)

    def dragging(self, tracks):
        # 按照行动轨迹先正向滑动，后反滑动
        button = self.dr.find_element_by_class_name('JDJRV-slide-btn')
        ActionChains(self.dr).click_and_hold(button).perform()
        tracks_backs = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]  # -20

        for track in tracks:
            ActionChains(self.dr).move_by_offset(xoffset=track, yoffset=0).perform()

        time.sleep(0.18)

        ActionChains(self.dr).move_by_offset(xoffset=-3, yoffset=0).perform()
        ActionChains(self.dr).move_by_offset(xoffset=4, yoffset=0).perform()

        time.sleep(0.7)
        ActionChains(self.dr).release().perform()
        pass
    

#参数1：1=下载素材并合并素材，3=开始登录
#参数2：是否启用chrome headless 模式、
# 参数3：登录滑块素材下载个数
jd = JD(3, False, 90)
jd.autologin("https://passport.jd.com/new/login.aspx","user","passwd")
