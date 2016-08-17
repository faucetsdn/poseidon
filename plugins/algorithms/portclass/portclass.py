import pandas as pd
import numpy as np
from sklearn.cross_validation import train_test_split
from sklearn import linear_model
from sklearn import preprocessing 
from sklearn.metrics import classification_report
import sys
import pika

wait = True
while wait:
    try:
        params = pika.ConnectionParameters(host='rabbitmq')
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange='topic_poseidon_internal', type='topic')
        out_queue_name = 'eval_algos_profileclass'
        result = channel.queue_declare(queue=out_queue_name, exclusive=True)
        in_queue_name = 'process_features_flowparser'
        result = channel.queue_declare(queue=in_queue_name, exclusive=True)
        wait = False
        print 'connected to rabbitmq...'
    except:
        print 'waiting for connection to rabbitmq...'
        time.sleep(2)
        wait = True

binding_keys = sys.argv[1:]
if not binding_keys:
    print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
    sys.exit(1)
for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_poseidon_internal',
                       queue='',
                       routing_key=binding_key)
print ' [*] Waiting for logs. To exit press CTRL+C'     

def plugin_example(stats_path, ports_classify):

	#Read in file 
	flow_df = pd.read_csv(stats_path,names=['srcip','srcport','dstip','dstport','proto','total_fpackets','total_fvolume',
                                              'total_bpackets','total_bvolume','min_fpktl','mean_fpktl','max_fpktl','std_fpktl',
                                              'min_bpktl','mean_bpktl','max_bpktl','std_bpktl','min_fiat','mean_fiat','max_fiat',
                                              'std_fiat','min_biat','mean_biat','max_biat','std_biat','duration','min_active',
                                              'mean_active','max_active','std_active','min_idle','mean_idle','max_idle','std_idle',
                                              'sflow_fpackets','sflow_fbytes','sflow_bpackets','sflow_bbytes','fpsh_cnt','bpsh_cnt',
                                              'furg_cnt','burg_cnt','total_fhlen','total_bhlen','misc'])

	#Remove uneccesary columns 
	flow_df = flow_df.drop('misc', axis=1)

	#Filter initial raw dataset to only have ports classified that are specefied 
	filtered_df = flow_df.loc[flow_df['dstport'].isin([53,443,80]) | flow_df['srcport'].isin([53,443,80])]  
	
	#Create stats only array
	stats = filtered_df.ix[:,'total_fpackets':]

	#Create ports only aray 
	ports = filtered_df.apply(lambda x: min(x['srcport'],x['dstport']),axis=1)
	
	#Scale stats info to be fed into classifier 
	scaled_stats = preprocessing.scale(stats)

	#Create test and training data 
	X_train, X_test, y_train, y_test = train_test_split(scaled_stats,ports.values, test_size=0.2, random_state=41) 

	#Create logistic regression model 
	lgs = linear_model.LogisticRegression(C=1e5)
	overall_accuracy = lgs.fit(X_train, y_train).score(X_test, y_test)
	print overall_accuracy

	#Classification Report for model 
	result = lgs.predict(X_test)
	class_report = classification_report(y_test, result)
	print class_report

	channel.basic_publish(exchange='topic_poseidon_internal',routing_key=routing_key, body=message)

    print ' [x] Sent %r:%r' % (routing_key, message)



channel.basic_consume('', queue=in_queue_name, no_ack=True)
channel.start_consuming()



