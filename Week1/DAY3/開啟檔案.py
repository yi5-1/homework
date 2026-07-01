path = 'C:\\Users\\TSIC\\Documents\\project\\Week1\\DAY3\\985ed9fd-c6a3-4421-9886-79621e170322.csv'
f = open(path,'r',newline='',encoding='utf-8')
a = f.read()
# print(a) #先查看檔案原始內容是啥
# print(type(a))# 再查看他類型是什麼
# print(len(a))#看有多長
b = a.split("\n") #決定用\n作為分割的依據
# print(b) #看一下分割完的內容
# print(b[0]) #第一格與excel內容去比對
# print(b[1])
# print(b[2])# 比對完前三筆確認是我要的
# print(len(b)) #查看總體的數量(列數)
#print
# print(b[3])
# print(len(b[3]))
c =[]#把每一列的每一行單獨存成list
for i in range(len(b)):#處理每一行
    c.append(str(b[i]).split(","))#把每行的數值換成str在透過split把,分隔的變成單獨的列表元素
    if( i <39): #過濾掉頭跟尾純中文的
        print(c[i][8])
print(c[1][1])