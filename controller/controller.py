import os
import time
import boto3
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
# initialise sqs client and read queue urls from file
sqs = boto3.client('sqs')
queues = open('/root/.aws/queues', 'r')
work_url = queues.readline()
unsolved_url = queues.readline()
solving_url = queues.readline()
queues.close()
# initialise empty work dictionary to maintain details of work
# initialise empty solved dictionary to track completion of work
work = {}
solved = {}

while True:
    try:
        # retrieve message from work queue
        response = sqs.receive_message(
            QueueUrl=work_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )

        message = response['Messages'][0]
        body = message['Body']
        attributes = message['MessageAttributes']
        receipt_handle = message['ReceiptHandle']
        # delete message from work queue
        sqs.delete_message(
            QueueUrl=work_url,
            ReceiptHandle=receipt_handle
        )
        # add work to work dictionary
        work[body] = {'width' : int(attributes['width']['StringValue']),
                      'height' : int(attributes['height']['StringValue']),
                      'thresh' : int(attributes['thresh']['StringValue']),
                      'zoom' : int(attributes['zoom']['StringValue']),
                      'focus' : list(map(float, attributes['focus']['StringValue'].strip('[]').split(','))),
                      'bounds' : list(map(float, attributes['bounds']['StringValue'].strip('[]').split(','))),
                      'frame-rate' : int(attributes['frame-rate']['StringValue']),
                      'frame-batch' : int(attributes['frame-batch']['StringValue']),
                      'frame-total' : int(attributes['frame-total']['StringValue']),
                      'time-out' : int(attributes['time-out']['StringValue'])
        }
        # add batches to solved dictionary 
        solved[body] = [False for _ in range(0, work[body]['frame-total'], work[body]['frame-batch'])]
        # send messages to unsolved queue 
        for batch in range(0, work[body]['frame-total'] // work[body]['frame-batch']):
            response = sqs.send_message(
                QueueUrl = unsolved_url,
                MessageBody = body,
                MessageAttributes={
                    'width': {
                        'DataType': 'String',
                        'StringValue': attributes['width']['StringValue']
                    },
                    'height': {
                        'DataType': 'String',
                        'StringValue': attributes['height']['StringValue']
                    },
                    'thresh': {
                        'DataType': 'String',
                        'StringValue': attributes['thresh']['StringValue']
                    },
                    'zoom': {
                        'DataType': 'String',
                        'StringValue': attributes['zoom']['StringValue']
                    },
                    'focus': {
                        'DataType': 'String',
                        'StringValue': attributes['focus']['StringValue']
                    },
                    'bounds': {
                        'DataType': 'String',
                        'StringValue': attributes['bounds']['StringValue']
                    },
                    'frames': {
                        'DataType': 'String',
                        'StringValue': str([batch * work[body]['frame-batch'], (batch + 1) * work[body]['frame-batch'] - 1])
                    },
                    'batch': {
                        'DataType': 'String',
                        'StringValue': str(batch)
                    },
                },
            )
    except:
        pass

    try:
        # retrieve message from solving queue
        response = sqs.receive_message(
            QueueUrl=solving_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )

        message = response['Messages'][0]
        body = message['Body']
        attributes = message['MessageAttributes']
        receipt_handle = message['ReceiptHandle']
        # delete message from solving queue
        sqs.delete_message(
            QueueUrl=solving_url,
            ReceiptHandle=receipt_handle
        )
        # add time batch began being solved to solved queue
        solved[body][int(attributes['batch']['StringValue'])] = float(attributes['time']['StringValue'])
    except:
        pass

    # loop through all work and every batch checking for frames
    delete = []
    for body in solved:
        work_solved = True

        for batch in range(len(solved[body])):
            batch_solved = True

            for frame in range(batch * work[body]['frame-batch'], batch * work[body]['frame-batch'] + work[body]['frame-batch']):
                path = Path('/root/.nfs/' + str(body) + str(frame) + '.png') 

                if path.exists() == False:
                    work_solved, batch_solved = False, False
            # set solved dictionary batch to true if all frames complete
            if batch_solved == True:
                solved[body][batch] = True
            # set solved dictionary batch to false if incorrectly labeled
            elif isinstance(solved[body][batch], bool):
                solved[body][batch] = False
            # set solved dictionary batch to false if not all frames complete and timed out
            elif isinstance(solved[body][batch], float) and time.time() - solved[body][batch] > work[body]['time-out']:
                solved[body][batch] = False
                # resend message to unsolved queue
                response = sqs.send_message(
                    QueueUrl = unsolved_url,
                    MessageBody = body,
                    MessageAttributes={
                        'width': {
                            'DataType': 'String',
                            'StringValue': str(work[body]['width'])
                        },
                        'height': {
                            'DataType': 'String',
                            'StringValue': str(work[body]['height'])
                        },
                        'thresh': {
                            'DataType': 'String',
                            'StringValue': str(work[body]['thresh'])
                        },
                        'zoom': {
                            'DataType': 'String',
                            'StringValue': str(work[body]['zoom'])
                        },
                        'focus': {
                            'DataType': 'String',
                            'StringValue': str(work[body]['focus'])
                        },
                        'bounds': {
                            'DataType': 'String',
                            'StringValue': str(work[body]['bounds'])
                        },
                        'frames': {
                            'DataType': 'String',
                            'StringValue': str([batch * work[body]['frame-batch'], (batch + 1) * work[body]['frame-batch'] - 1])
                        },
                        'batch': {
                            'DataType': 'String',
                            'StringValue': str(batch)
                        },
                    },
                )

        try:
            # load all frames, render video and delete all frames
            if work_solved == True:
                images = []

                for frame in range(len(solved[body]) * work[body]['frame-batch']):
                    img = Image.open('/root/.nfs/' + str(body) + str(frame) + '.png')
                    images.append(img.copy())
                    img.close()
                    
                images[0].save('/root/.nfs/' + str(body) + '.png', save_all=True, append_images=(((500 // work[body]['frame-rate']) - 1) * [images[0]] + images[1:] + ((500 // work[body]['frame-rate']) - 2) * [images[-1]] + images[:0:-1]), duration=work[body]['frame-rate'], loop=0)
                images[0].save('/root/.nfs/' + str(body) + '.gif', save_all=True, append_images=(((500 // work[body]['frame-rate']) - 1) * [images[0]] + images[1:] + ((500 // work[body]['frame-rate']) - 2) * [images[-1]] + images[:0:-1]), duration=work[body]['frame-rate'], loop=0)
                
                for frame in range(len(solved[body]) * work[body]['frame-batch']):
                    images[frame].close()
                    os.remove('/root/.nfs/' + str(body) + str(frame) + '.png')
                
                delete.append(body)
        except:
            pass
    # delete work from solved dictionary
    for body in delete:
        del solved[body]