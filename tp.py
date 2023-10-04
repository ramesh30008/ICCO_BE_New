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
        rec = len(org_ykeys)
        if "Total" in org_ykeys:
           rec = len(org_ykeys) - 1 
        data_dict["records"] = rec
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
 
    def getPageData(self, key, page_no, no_of_rows):
        data = self.redis.get(key)
        data = eval(data)
        tykeys = data["tykeys"]
        if no_of_rows=="all":
           no_of_rows = len(tykeys) 
           ntykeys = tykeys[:]
        else:
           ntykeys = tykeys[(page_no-1) * no_of_rows : ((page_no-1) * no_of_rows) + no_of_rows]
        if "Total" in ntykeys:
            ntykeys.remove("Total")
            ntykeys.insert(0, "Total") 
        print ("ntykeys: ", ntykeys)
        ntdata = []
        for col_data in data["tdata"]:
           tmp = {} 
           default_keys = col_data.keys()
           #print ("col_data", col_data) 
           for yelm in ntykeys:
              if not str(col_data.get(yelm, "")): continue
              tmp[yelm] = col_data[yelm]
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
              if "d_date" in default_keys:
                 tmp["d_date"] = col_data["d_date"]
              if "name" in default_keys:
                 tmp["name"] = col_data["name"]
              if "name_2" in default_keys:
                 tmp["name_2"] = col_data["name_2"]
           ntdata.append(tmp)             
        no_of_pages = int(math.ceil(len(tykeys)/no_of_rows))
        rec = len(tykeys)
        if "Total" in tykeys:
           rec = rec - 1 
        return {"tykeys": ntykeys, "tdata": ntdata, "txkeys": data["txkeys"], "key": key, "total_pages": no_of_pages, "records": rec}  

    def sort_dict_list(dict_list, order_list):
        # Sort the list of dictionaries based on the order list
        sorted_list = sorted(dict_list, key=lambda x: order_list.index(x.get('subscription')) if x.get('subscription') in order_list else len(order_list))
        print(sorted_list)
        # Append any items without a matching value to the end of the sorted list
        for item in dict_list:
            if item not in sorted_list:
                sorted_list.append(item)
        return sorted_list 
    
    def getAllGraphData(self, data_dict):
        key, color_dict_list, date_str, ykeys = data_dict["key"],data_dict["color_dict"], data_dict["date_str"], data_dict['ykeys']
        color_dict = {}
        for temp_dict in color_dict_list:
            color_dict[temp_dict["subscription"]] = temp_dict["color"]
        data = self.redis.get(key)
        #print(data)
        data = eval(data)
        ntykeys = data["tykeys"]
        if "Total" in ntykeys:
            ntykeys.remove("Total")
        ntdata = []
        other_color = color_dict.get("others", "#2bd")
        total_cnt = 0
        d = []
        for col_data in data["tdata"]:
           if col_data["d_date"]!= date_str:continue
           default_keys = col_data.keys()
           #print ("col_data", col_data)
           for yelm in ntykeys:
              tmp = {}
              if not str(col_data.get(yelm, "")): continue
              total_cnt+=col_data[yelm]
              if "d_date" in default_keys:
                 tmp["date"] = col_data["d_date"]
              if "name" in default_keys:
                 tmp["subscription"] = yelm
              tmp['color'] = color_dict.get(yelm, other_color)
              tmp["loader"] = "false"
              tmp["price"] = col_data[yelm]
              ntdata.append(tmp)
              print(tmp)
        for tmp in ntdata:
            for yelm in ntykeys:
                if tmp['subscription'] != yelm:continue
                perc = tmp['price']/total_cnt * 1.0
                print(perc)
                tmp["p"] = round(perc, 2)*100
                tmp['total'] = total_cnt
                print(tmp)
        sorted_list = sort_dict_list(ntdata, ykeys) 
        return {"data": sorted_list} 

if __name__=="__main__":
    obj = table_paginate('142.93.208.71')
    data_dict = {
    "key": "6c125b92-6de6-406f-b26b-d0182af914ea",
    "color_dict": [
        {
            "subscription": "drzkpltest",
            "color": "#b5179e"
        },
        {
            "subscription": "4242sjv1043-1",
            "color": "#f72585"
        },
        {
            "subscription": "4242sll2062-1",
            "color": "#7209b7"
        },
        {
            "subscription": "4242sll2062-0",
            "color": "#3a0ca3"
        },
        {
            "subscription": "4242-sze-1042-0",
            "color": "#3f37c9"
        },
        {
            "subscription": "4242-sze-1042-5",
            "color": "#4361ee"
        },
        {
            "subscription": "drmgmtzkpltest",
            "color": "#37e1c5"
        },
        {
            "subscription": "Others",
            "color": "#2bd"
        }
    ],
    "date_str": "2023-02-24",
    "ykeys":["4242sjv1043-1", "drzkpltest", "Others", "4242-sze-1042-5"]
}
    print(obj.getAllGraphData(data_dict))
    
