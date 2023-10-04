from redis import Redis
import uuid
import pickle
import math

PASSWORD = "p@ss$12E45"
class table_paginate:
    def __init__(self, hhost="localhost", pport=6379):        
        self.redis = Redis(host=hhost, port=pport, password=PASSWORD)

    def storeData(self, data_dict):
        print ("1")
        mkey = str(uuid.uuid4())
        org_ykeys = data_dict["tykeys"]
        query_string = 'SET %s "%s"' %(mkey, pickle.dumps(data_dict))
        query_string2 = 'SET %s_oykeys "%s"' %(mkey, pickle.dumps(org_ykeys))
        print ("1-1")
           
        if 1:#try:
           self.redis.set("%s_oykeys" %mkey, str(org_ykeys))
           self.redis.set("%s" %mkey, str(data_dict))
        print ("2")
        #except Exception as e:
        #    print ("Error while executing union_search: \'"+query_string+"\'")
        #    print (e)

        no_of_rows = 10#data_dict["no_of_rows"]
        page_no = 1
        no_of_pages = int(math.ceil(len(org_ykeys)/no_of_rows))
        print ("3")
        data_dict = self.getPageData(mkey, page_no, no_of_rows) 
        print ("4")
        data_dict["total_pages"] = no_of_pages
        rec = len(org_ykeys)
        if "Total" in org_ykeys:
           rec = len(org_ykeys) - 1 
        data_dict["records"] = rec
        print ("5")
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
        ykeyname = data["txkeys"][0]

        tykeys = [[i1, e[ykeyname]] for i1, e in enumerate(data["tdata"])]
        if no_of_rows=="all":
           no_of_rows = len(tykeys) 
           ntykeys = tykeys[:]
        else:
           ntykeys = tykeys[(page_no-1) * no_of_rows : ((page_no-1) * no_of_rows) + no_of_rows]

        ntdata = []
        indexes_allowed = [e[0] for e in ntykeys]   
        for i1, row_data in enumerate(data["tdata"]):
           if i1 not in indexes_allowed: continue
           ntdata.append(row_data)             

        no_of_pages = int(math.ceil(len(tykeys)/no_of_rows))
        rec = len(tykeys)
        if "Total" in [e[1] for e in tykeys]:
           rec = rec - 1 
        return {"tykeys": ntykeys, "tdata": ntdata, "txkeys": data["txkeys"], "key": key, "total_pages": no_of_pages, "records": rec}  

    def sort_dict_list(self, dict_list, order_list):
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
                perc = round(tmp['price']/total_cnt * 1.0,2)
                #tmp["p"] = round(perc*100,2)
                tmp["p"] = round(perc*100,2)
                tmp['total'] = total_cnt
        sorted_list = self.sort_dict_list(ntdata, ykeys)
        return {"data": sorted_list, 'total':total_cnt}



if __name__=="__main__":
    data_dict = {"gdata":[{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":48.21,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":12.28,"4302-MNX-2_Curr":"USD","Others":157.81,"Others_Curr":"USD","Total":312.75,"d_date":"2022-11-23","gap":"2px","name":"23-Nov","opacity":0.7},{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":48.02,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":12.13,"4302-MNX-2_Curr":"USD","Others":157.55,"Others_Curr":"USD","Total":312.15,"d_date":"2022-11-24","gap":"2px","name":"24-Nov","opacity":0.7},{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":48.12,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":12.32,"4302-MNX-2_Curr":"USD","Others":157.93,"Others_Curr":"USD","Total":312.82,"d_date":"2022-11-25","gap":"2px","name":"25-Nov","opacity":0.7},{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":11.93,"4302-MNX-2_Curr":"USD","Others":157.16,"Others_Curr":"USD","Total":310.64,"d_date":"2022-11-26","gap":"2px","name":"26-Nov","opacity":0.7},{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":11.78,"4302-MNX-2_Curr":"USD","Others":156.85,"Others_Curr":"USD","Total":310.18,"d_date":"2022-11-27","gap":"2px","name":"27-Nov","opacity":0.7},{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":11.78,"4302-MNX-2_Curr":"USD","Others":156.85,"Others_Curr":"USD","Total":310.18,"d_date":"2022-11-28","gap":"2px","name":"28-Nov","opacity":0.7},{"4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4302-MNX-2":11.78,"4302-MNX-2_Curr":"USD","Others":156.85,"Others_Curr":"USD","Total":310.18,"d_date":"2022-11-29","gap":"2px","name":"29-Nov","opacity":0.7}],"gxkeys":["23-Nov","24-Nov","25-Nov","26-Nov","27-Nov","28-Nov","29-Nov"],"gykeys":["4261-SPO-43","4297-MSY-85","4295-MBS-84","4295-M24-83","4261-SYY-4","4261-SHB-5","4302-MNX-2","Others"],"tdata":[{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":48.21,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":12.23,"4302-MLI-1_Curr":"USD","4302-MMX-89":10.11,"4302-MMX-89_Curr":"USD","4302-MNX-2":12.28,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":312.75,"d_date":"2022-11-23","gap":"2px","name":"23-Nov","opacity":0.7},{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":48.02,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":12.13,"4302-MLI-1_Curr":"USD","4302-MMX-89":9.95,"4302-MMX-89_Curr":"USD","4302-MNX-2":12.13,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":312.15,"d_date":"2022-11-24","gap":"2px","name":"24-Nov","opacity":0.7},{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":48.12,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":12.32,"4302-MLI-1_Curr":"USD","4302-MMX-89":10.14,"4302-MMX-89_Curr":"USD","4302-MNX-2":12.32,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":312.82,"d_date":"2022-11-25","gap":"2px","name":"25-Nov","opacity":0.7},{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":11.93,"4302-MLI-1_Curr":"USD","4302-MMX-89":9.76,"4302-MMX-89_Curr":"USD","4302-MNX-2":11.93,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":310.64,"d_date":"2022-11-26","gap":"2px","name":"26-Nov","opacity":0.7},{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":11.78,"4302-MLI-1_Curr":"USD","4302-MMX-89":9.6,"4302-MMX-89_Curr":"USD","4302-MNX-2":11.78,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":310.18,"d_date":"2022-11-27","gap":"2px","name":"27-Nov","opacity":0.7},{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":11.78,"4302-MLI-1_Curr":"USD","4302-MMX-89":9.6,"4302-MMX-89_Curr":"USD","4302-MNX-2":11.78,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":310.18,"d_date":"2022-11-28","gap":"2px","name":"28-Nov","opacity":0.7},{"4261-MHE-42":5.89,"4261-MHE-42_Curr":"USD","4261-MME-41":5.89,"4261-MME-41_Curr":"USD","4261-PCT-36":5.89,"4261-PCT-36_Curr":"USD","4261-SHB-5":17.66,"4261-SHB-5_Curr":"USD","4261-SPO-43":47.1,"4261-SPO-43_Curr":"USD","4261-SQO-44":11.78,"4261-SQO-44_Curr":"USD","4261-SYY-4":17.66,"4261-SYY-4_Curr":"USD","4278-MLI-1":5.89,"4278-MLI-1_Curr":"USD","4278-SCT-36":5.89,"4278-SCT-36_Curr":"USD","4278-SPO-43":5.89,"4278-SPO-43_Curr":"USD","4286-MLI-1":5.89,"4286-MLI-1_Curr":"USD","4286-SYY-4":5.89,"4286-SYY-4_Curr":"USD","4289-MME-41":5.89,"4289-MME-41_Curr":"USD","4289-SPO-43":5.89,"4289-SPO-43_Curr":"USD","4292-MNX-2":5.89,"4292-MNX-2_Curr":"USD","4295-M24-83":19.71,"4295-M24-83_Curr":"USD","4295-MBS-84":19.71,"4295-MBS-84_Curr":"USD","4296-MNX-2":5.89,"4296-MNX-2_Curr":"USD","4297-MSY-85":19.71,"4297-MSY-85_Curr":"USD","4298-MNX-2":5.89,"4298-MNX-2_Curr":"USD","4298-MTW-3":5.89,"4298-MTW-3_Curr":"USD","4299-MHE-42":5.89,"4299-MHE-42_Curr":"USD","4299-MTW-3":5.89,"4299-MTW-3_Curr":"USD","4301-MLI-1":5.89,"4301-MLI-1_Curr":"USD","4301-MNX-2":5.89,"4301-MNX-2_Curr":"USD","4302-MLI-1":11.78,"4302-MLI-1_Curr":"USD","4302-MMX-89":9.6,"4302-MMX-89_Curr":"USD","4302-MNX-2":11.78,"4302-MNX-2_Curr":"USD","4303-MHE-42":5.89,"4303-MHE-42_Curr":"USD","4303-MTW-3":5.89,"4303-MTW-3_Curr":"USD","4304-MTW-3":5.89,"4304-MTW-3_Curr":"USD","Total":310.18,"d_date":"2022-11-29","gap":"2px","name":"29-Nov","opacity":0.7}],"txkeys":["23-Nov","24-Nov","25-Nov","26-Nov","27-Nov","28-Nov","29-Nov"],"tykeys":["Total","4261-MHE-42","4261-MME-41","4261-PCT-36","4261-SHB-5","4261-SPO-43","4261-SQO-44","4261-SYY-4","4278-MLI-1","4278-SCT-36","4278-SPO-43","4286-MLI-1","4286-SYY-4","4289-MME-41","4289-SPO-43","4292-MNX-2","4295-M24-83","4295-MBS-84","4296-MNX-2","4297-MSY-85","4298-MNX-2","4298-MTW-3","4299-MHE-42","4299-MTW-3","4301-MLI-1","4301-MNX-2","4302-MLI-1","4302-MMX-89","4302-MNX-2","4303-MHE-42","4303-MTW-3","4304-MTW-3"]}
    obj = table_paginate('142.93.208.71')
    #obj.storeData(data_dict)
    #print (obj.getPageData("key1", 2, 10))
    #print (obj.sortData("key1", 1, 0))
    obj.delete_key("abc2214c-5f11-4f89-b390-1b6364b2bdab")
