import time
import boto3
import numpy as np
from PIL import Image, ImageDraw
# initialise sqs client and read queue urls from file
sqs = boto3.client('sqs')
queues = open('/root/.aws/queues', 'r')
queues.readline()
unsolved_url = queues.readline()
solving_url = queues.readline()
queues.close()
# generates mandelbrot frames
def mandelbrot(name, width, height, thresh, zoom, focus, bounds, frames):
    img = Image.new('HSV', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    focus = np.array(focus, dtype=float)
    bounds = np.array(bounds, dtype=float).reshape(2,2)
    for _ in range(frames[0]):
        bounds -= (bounds-focus)/zoom
    for frame in range(frames[0], frames[1] + 1):
        for x in range(width):
            for y in range(height):
                i = 0
                z = 0
                c = complex(bounds[0,0] + (x / width) * (bounds[1,0] - bounds[0,0]), bounds[1,1] + (y / height) * (bounds[0,1] - bounds[1,1]))
                while i < thresh and abs(z) <= 2:
                    i += 1
                    z = z*z + c
                hue = int(255 * i / thresh)
                saturation = 255
                value = 255 if i < thresh else 0
                draw.point([x, y], (hue, saturation, value))
        img.convert('RGB').save('/root/.nfs/' + str(name) + str(frame) + '.png', 'PNG')
        bounds -= (bounds-focus)/zoom
    img.close()

# initialise empty work dictionary to maintain details of work
work = {}

while True:
    try:
        # retrieve message from unsolved queue
        response = sqs.receive_message(
            QueueUrl=unsolved_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )

        message = response['Messages'][0]
        body = message['Body']
        attributes = message['MessageAttributes']
        receipt_handle = message['ReceiptHandle']
        # delete message from unsolved queue
        sqs.delete_message(
            QueueUrl=unsolved_url,
            ReceiptHandle=receipt_handle
        )
        # add work to work dictionary
        work[body] = {'width' : int(attributes['width']['StringValue']),
                      'height' : int(attributes['height']['StringValue']),
                      'thresh' : int(attributes['thresh']['StringValue']),
                      'zoom' : int(attributes['zoom']['StringValue']),
                      'focus' : list(map(float, attributes['focus']['StringValue'].strip('[]').split(','))),
                      'bounds' : list(map(float, attributes['bounds']['StringValue'].strip('[]').split(','))),
                      'frames' : list(map(int, attributes['frames']['StringValue'].strip('[]').split(','))),
                      'batch' : int(attributes['batch']['StringValue'])
        }
        # send message to solving queue 
        response = sqs.send_message(
            QueueUrl = solving_url,
            MessageBody = body,
            MessageAttributes={
                'batch': {
                    'DataType': 'String',
                    'StringValue': str(work[body]['batch'])
                },
                'time': {
                    'DataType': 'String',
                    'StringValue': str(time.time())
                },
            },
        )
        # call mandelbrot with work
        mandelbrot(body, work[body]['width'], work[body]['height'], work[body]['thresh'], work[body]['zoom'], work[body]['focus'], work[body]['bounds'], work[body]['frames'])
    except:
        pass