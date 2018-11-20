
#图像处理标准库
from PIL import Image   
#web测试
from selenium import webdriver
#鼠标操作
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
#等待时间 产生随机数 
import time,random,datetime,os
import math
from functools import reduce
import operator

class JD(object):

    def __init__(self,step,is_headless,down_img_count,img_dir="./images/jd/"):
         #设置
        chrome_options = Options()
        # 无头模式启动
        if is_headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument("--start-maximized")
        # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--disable-gpu')
        # 设置屏幕器宽高
        chrome_options.add_argument("--window-size=1440,750");

        self.dr=webdriver.Chrome(executable_path=(r"./chromedriver_win32/chromedriver.exe"), chrome_options=chrome_options)
        self.dr.maximize_window();
        self.step=step;
        self.img_dir=img_dir
        self.down_dir=r"./images/jd4/";
        self.down_img_count=down_img_count;

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
    
    def compare2(self,image1,image2):
        '''
        :图片相识度简单对比 图片越像返回值越趋近于0，返回 0-1 认为图片非常相似
        :param image1: 图片1对象
        :param image2: 图片2对象
        :return: 返回对比的结果
        '''

        histogram1 = image1.histogram()
        histogram2 = image2.histogram()

        differ = math.sqrt(reduce(operator.add, list(map(lambda a,b: (a-b)**2,histogram1, histogram2)))/len(histogram1))
        return differ/100

    def autologin(self,url,username,password):  
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
        lotab[0].click();
        time.sleep(1);
        name=self.dr.find_element_by_id("loginname");
        name.send_keys(username);
        time.sleep(1);
        pwd=self.dr.find_element_by_id("nloginpwd");
        pwd.send_keys(password);
        time.sleep(1.3);
        logbtn=self.dr.find_element_by_id("loginsubmit")
        logbtn.click();

        slide=self.dr.find_element_by_class_name("JDJRV-suspend-slide");
        if slide:
            print("进入滑块验证码流程");
            if self.step==1:
                print("第一次登录，开始下载素材：");
                for i in range(self.down_img_count-1):
                    #self.get_images(r"D:/learn/python3.6/PythonTest/spiders/images/jd/1542264153.554946.png");
                    self.get_images();
            elif self.step==2:
                print("已下载过素材,合并素材：");
                img_path=r"./images/jd3/";
                i=1;
                while i<=10:
                    if os.path.exists(img_path+str(i)+"d.png") and os.path.exists(img_path+str(i)+"u.png"):
                        imgu=Image.open(img_path+str(i)+"u.png");
                        imgd=Image.open(img_path+str(i)+"d.png");
                        img_temp=imgu.crop((0,0,imgu.width,imgu.height/2))
                        #img_temp.show();
                        imgd.paste(img_temp,(0,0));
                        imgd.save(self.down_dir+str(i)+"m.png");
                        print("合并第"+str(i)+"张")
                    i=i+1;
            elif self.step==3:
                print("已有素材,开始登录：");
                if slide:
                    for i in range(50):                
                        self.do_login();
                        time.sleep(1.7);
                        title=self.dr.title;
                        if title=="京东-欢迎登录":
                            continue;
                        else:
                            print("登录成功："+title);
                            break;
                else:
                    time.sleep(1.2);
                    logbtn.click();          
        
        print('结束时间',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        pass
    
    def do_login(self):
        curent_img= self.get_images();    
        curent_img.save(self.img_dir+'current.png');            
        files= os.listdir(self.down_dir)
        simi_dict=dict();

        for f in files:   
            temp_img= Image.open(self.down_dir+f);                 
            simi_val=self.compare2(temp_img,curent_img);
            simi_dict[f]=simi_val;
        
        mini=min(simi_dict, key=simi_dict.get);
        image1=Image.open(self.down_dir+mini);
        gap= self.get_gap(image1,curent_img);
        print(gap);

        track=self.get_track7(gap+20.85);
        self.dragging(track);
        pass
    
    def dragging(self,tracks):
         # 按照行动轨迹先正向滑动，后反滑动
        button = self.dr.find_element_by_class_name('JDJRV-slide-btn')
        ActionChains(self.dr).click_and_hold(button).perform()
        tracks_backs=[-3,-3,-2,-2,-2,-2,-2,-1,-1,-1] #-20

        for track in tracks:
            ActionChains(self.dr).move_by_offset(xoffset=track, yoffset=0).perform()

        time.sleep(0.18)
        #反向滑动
        # for back in tracks_backs:
        #      ActionChains(self.dr).move_by_offset(xoffset=back, yoffset=0).perform()

        ActionChains(self.dr).move_by_offset(xoffset=-3, yoffset=0).perform()
        ActionChains(self.dr).move_by_offset(xoffset=3, yoffset=0).perform()

        time.sleep(0.7)
        ActionChains(self.dr).release().perform()
        pass;
    
    def get_images(self,find_this_img=""):
        time.sleep(0.8)    
        btn_refesh=self.dr.find_element_by_class_name('JDJRV-img-refresh')
        img=self.dr.find_element_by_class_name('JDJRV-bigimg')
        location=img.location
        size=img.size
        left=location['x']
        top=location['y']
        right=left+size['width']
        bottom=top+size['height']

        time.sleep(0.99)    
        page_snap_obj=self.get_snap()
        image_obj=page_snap_obj.crop((left,top,right,bottom))

        #图片相似才保存
        if find_this_img!="":            
            dog=Image.open(find_this_img)
            if self.compare2(dog,image_obj)<0.6:
                image_obj.save(self.img_dir+str(time.time())+'.png')
        else:
            image_obj.save(self.img_dir+str(time.time())+'.png')
        if self.step==1:
            btn_refesh.click();
        return image_obj

    def get_snap(self):
        """
        屏幕截图对象
        """ 
        self.dr.save_screenshot(self.img_dir+'full_snap.png')
        page_snap_obj=Image.open(self.img_dir+'full_snap.png');
        return page_snap_obj;


#参数1：1=下载素材，2=开始合并素材，3=开始登录
#参数2：是否启用chrome headless 模式、
#参数3：登录滑块素材下载个数
jd=JD(3,False,90);
jd.autologin("https://passport.jd.com/new/login.aspx","用户名","密码")
