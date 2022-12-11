# encoding:utf-8

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from PIL import Image
import pandas as pd
import time
import numpy as np
import ddddocr
import csv
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

chrome_options = webdriver.ChromeOptions()
# 使用headless无界面浏览器模式
# chrome_options.add_argument('--headless')       # 增加无界面选项
chrome_options.add_argument('--disable-gpu')    # 保证定位

# 处理SSL证书错误问题
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
 
# 忽略无用的日志
chrome_options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
    'Connection': 'close'
}

def veryCode_transform(img_name):
    img = Image.open("veryCode.jpg")
    img_rgb = img.convert('RGB')
    img_array = np.array(img_rgb)

    img_width = img.size[0]
    img_height = img.size[1]

    for i in range(0, img_height):
        for j in range(0, img_width):
            if img_array[i, j][0] == img_array[i, j][1] == img_array[i, j][2]:
                img_array[i, j] = [255, 255, 255]
            else:
                img_array[i, j] = [0, 0, 0]

    img2 = Image.fromarray(img_array)
    img2.save("veryCode2.png", "PNG")

    ocr = ddddocr.DdddOcr()
    res = ocr.classification(img2)

    return res


if __name__ == "__main__":
    url = "https://wap.js.10086.cn/nact/resource/0000/html/login.html?redirectURL=https://wap.js.10086.cn/mb_nact/new/yxwap/client/getAuth?actNum=700015452r93uhj7&actRedirectUrl=aHR0cDovL3dhcC5qcy4xMDA4Ni5jbi9tYl9uYWN0L25ldy9hY3QtZnJvbnQvY2ovY2owMjIvbWFpbi5odG1sP2FjdE51bT03MDAwMTU0NTJyOTN1aGo3JmZ4bW9iaWxlPVo1MDg3MjEw"

    browser = webdriver.Chrome(options=chrome_options)
    browser.implicitly_wait(5)  # 隐式等待，直至页面弹出
    browser.get(url)

    # 读取源数据
    df = pd.read_csv("Demo.csv", encoding='gbk')

    # 创建输出文件
    f = open("Demo-trans.csv", 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(f)
    csv_writer.writerow(['号码', '密码', '状态', "是否抽奖", "剩余流量"])

    for index, row in df.iterrows():
        mobile = row["号码"]        # 号码
        password = row["密码"]      # 密码
        password_type = "ERROR"     # 服务密码等状态
        award_type = "否"           # 是否抽奖 
        flow_reaminder = 0          # 剩余流量

        # 测试号码
        # mobile = "13616215462"
        # password = "646695"

        print("第" + str(index) + "个号码")
        print("测试号码：" + str(mobile) + "; 密码：" + str(password))

        # 切换为服务密码模式
        login_type = browser.find_element(By.XPATH, '//*[@id="loginMain"]/form/div[1]/span[2]/label')
        login_type.click()

        # 输入号码
        input_tel = browser.find_element(By.XPATH, '//*[@id="telNum1"]')
        input_tel.send_keys(str(mobile))

        # 输入服务密码
        input_pwd = browser.find_element(By.XPATH, '//*[@id="val"]')
        input_pwd.send_keys(str(password))

        # 获取验证码图片
        time.sleep(2)
        img_check = browser.find_element(By.XPATH, '//*[@id="loginMain"]/form/div[2]/div[4]/img')
        with open("veryCode.jpg", "wb") as f:
            f.write(img_check.screenshot_as_png)

        # OCR：图片转字符
        veryCode_content = veryCode_transform("veryCode.jpg")
        print(veryCode_content)
        time.sleep(3)

        # 验证码输入
        input_check = browser.find_element(By.XPATH, '//*[@id="imageCode1"]')
        input_check.send_keys(veryCode_content)

        # 点击登录
        btn_login = browser.find_element(By.XPATH, '//*[@id="loginMain"]/form/button')
        btn_login.click()

        time.sleep(3)

        try:    # 进入抽奖页面

            password_type = "服务密码正确"

            # 剩余流量
            flow = browser.find_element(By.XPATH, '//*[@id="js-x-exchangepoint"]')
            flow_reaminder = flow.text
            print(flow_reaminder)

            # 点击抽奖
            btn_award = browser.find_element(By.XPATH, '//*[@id="js-game"]/div[2]')
            btn_award.click()

            time.sleep(3)

            try:
                # 点击抽奖确认
                btn_confirm = browser.find_element(By.XPATH, '//*[@id="js-dialog-exchange"]/div/div/div[3]/span[2]')
                btn_confirm.click()

                time.sleep(6)

                # 浮动变化后，再点击抽奖
                btn_award = browser.find_element(By.XPATH, '//*[@id="js-game"]/div[2]')
                ActionChains(browser).move_to_element_with_offset(flow, 0, 800).click().perform()          # 鼠标左键
                # ActionChains(browser).move_to_element_with_offset(flow, 0, 800).context_click().perform()   # 鼠标右键

            except:
                # 浮动变化后，再点击抽奖
                btn_award = browser.find_element(By.XPATH, '//*[@id="js-game"]/div[2]')
                btn_award.click()

            award_result = browser.find_element(By.XPATH, '//*[@id="js-dialog-notice"]/div/div/div[2]')
            award_type = award_result.text

            print()
            print(award_type)
        
        except: # 出现报错

            try:
                err_message = browser.find_element(By.XPATH, '//*[@id="loginMain"]/form/div[3]')
                password_type = err_message.text

                print(password_type)
            
            except:
                
                password_type = "不符合目标用户"

        time.sleep(3)
        browser.get(url)

        print("**********************************")

        csv_writer.writerow([mobile, password, password_type, award_type, flow_reaminder])
            

  