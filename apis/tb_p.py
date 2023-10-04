from redis import Redis
import uuid
import pickle
import math

PASSWORD = "p@ss$12E45"
class table_paginate:
    def __init__(self, hhost="localhost", pport=6379):        
        self.redis = Redis(host=hhost, port=pport, password=PASSWORD)

    def storeData(self, data_dict):
        mkey = str(uuid.uuid4())
        org_ykeys = data_dict["tykeys"]
        query_string = 'SET %s "%s"' %(mkey, pickle.dumps(data_dict))
        query_string2 = 'SET %s_oykeys "%s"' %(mkey, pickle.dumps(org_ykeys))
           
        if 1:#try:
           self.redis.set("%s_oykeys" %mkey, str(org_ykeys))
           self.redis.set("%s" %mkey, str(data_dict))
        #except Exception as e:
        #    print ("Error while executing union_search: \'"+query_string+"\'")
        #    print (e)

        no_of_rows = 10#data_dict["no_of_rows"]
        page_no = 1
        no_of_pages = int(math.ceil(len(org_ykeys)/no_of_rows))
        data_dict = self.getPageData(mkey, page_no, no_of_rows) 
        data_dict["total_pages"] = no_of_pages
        data_dict["records"] = len(org_ykeys) 
        return data_dict

    def delete_key(self, key):
        print ("redis", self.redis.keys("*-*"))
        #self.redis.delete(key)
        return 

    def sortData(self, key, column_id, sort_order):
        data = self.redis.get(key)
        data = eval(data)
        ndata = []
        if sort_order==2:
           ndata = self.redis.get(key+"_oykeys")
           ndata = eval(ndata)
        else:
           ykeys = data["tykeys"]
           xkey = "" 
           if column_id!=-1:
              xkey = data["txkeys"][column_id]
              col_data = data["tdata"][column_id]
              tmp = [] 
              for yelm in ykeys:
                  tmp.append([col_data.get(yelm, 0), yelm])
              tmp.sort()
              if sort_order==1:
                 tmp.reverse()
              ndata = [e[1] for e in tmp] 
           else:
              ykeys.sort()  
              if sort_order==1:
                 ykeys.reverse()
              ndata = ykeys[:]  

        data["tykeys"] = ndata[:]
        try:
           self.redis.set("%s" %key, str(data))
        except Exception as e:
            print ("Error while executing")
            print (e)
              
        page_no = 1
        no_of_rows = 10
        data_dict = self.getPageData(key, page_no, no_of_rows) 
        #data_dict["total_pages"] = no_of_pages
        data_dict["records"] = len(ndata) 
        return data_dict
 
    def getAllGraphData(self, key, page_no, no_of_rows, color_dict, date_str):
        data = self.redis.get(key)
        print(data)
        data = eval(data)
        ntykeys = data["tykeys"]
        if "Total" in ntykeys:
            ntykeys.remove("Total")
        ntdata = []
        other_color = color_dict["others"]
        total_cnt = 0
        for col_data in data["tdata"]:
           tmp = {}
           if col_data["d_date"]!= date_str:continue
           default_keys = col_data.keys()
           #print ("col_data", col_data) 
           for yelm in ntykeys:
              if not str(col_data.get(yelm, "")): continue
              tmp[yelm] = col_data[yelm]
              total_cnt+=tmp[yelm]        
              if "d_date" in default_keys:
                 tmp["d_date"] = col_data["d_date"]
              if yelm+"_Curr" in default_keys:
                 tmp[yelm+"_Curr"] = col_data[yelm+"_Curr"]
              if yelm+"_cur" in default_keys:
                 tmp[yelm+"_cur"] = col_data[yelm+"_cur"]
              if yelm+"_CID" in default_keys:
                 tmp[yelm+"_CID"] = col_data[yelm+"_CID"]
              if yelm+"_P" in default_keys:
                 tmp[yelm+"_P"] = col_data[yelm+"_P"]
              if yelm+"_A" in default_keys:
                 tmp[yelm+"_A"] = col_data[yelm+"_A"]
              if "name" in default_keys:
                 tmp["name"] = col_data["name"]
              if "name_2" in default_keys:
                 tmp["name_2"] = col_data["name_2"]
              tmp['color'] = color_dict.get( col_data["name"], other_color)
           ntdata.append(tmp)   
        for tmp in ntdata:
            for yelm in ntykeys:
                if not tmp.get(yelm, ""):continue         
                perc = tmp.get[yelm]/total_cnt * 1.0
                tmp[yelm+"_Per"] = round(perc, 2) 
        return {"tykeys": ntykeys, "tdata": ntdata, "txkeys": data["txkeys"], "key": key}    

if __name__=="__main__":
    obj = table_paginate('142.93.208.71')
    #obj.storeData(data_dict)
    print (obj.getPageData("14c7c8cf-8dd1-444d-a18a-caf321dc2011", 2, 10))
    #print (obj.sortData("key1", 1, 0))
    #obj.delete_key("abc2214c-5f11-4f89-b390-1b6364b2bdab")
