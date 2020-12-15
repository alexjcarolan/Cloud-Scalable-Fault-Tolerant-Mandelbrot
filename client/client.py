import boto3
import argparse

parser = argparse.ArgumentParser(description="Mandelbrot zoom", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--body", default='zoom', type=str, help="Message body")
parser.add_argument("--width", default='1000', type=str, help="Image width")
parser.add_argument("--height", default='1000', type=str, help="Image height")
parser.add_argument("--thresh", default='50', type=str, help="Mandelbrot threshold")
parser.add_argument("--zoom", default='50', type=str, help="Zoom factor")
parser.add_argument("--focus", default='[0,1]', type=str, help="Focus point")
parser.add_argument("--bounds", default='[-2,-2,2,2]', type=str, help="Initial bounds")
parser.add_argument("--frame-rate", default='20', type=str, help="Frame rate")
parser.add_argument("--frame-batch", default='100', type=str, help="Frame batch")
parser.add_argument("--frame-total", default='1500', type=str, help="Frame total")
parser.add_argument("--time-out", default='1200', type=str, help="Time out")
args = parser.parse_args()
# initialise sqs client and read queue url from file
sqs = boto3.client('sqs')
queues = open('C:\\Users\\Alex\\.aws\\queues', 'r')
work_url = queues.readline()
queues.close()
# send message to work queue
response = sqs.send_message(
    QueueUrl = work_url,
    MessageBody = args.body,
    MessageAttributes={
        'width': {
            'DataType': 'String',
            'StringValue': args.width
        },
        'height': {
            'DataType': 'String',
            'StringValue': args.height
        },
        'thresh': {
            'DataType': 'String',
            'StringValue': args.thresh
        },
        'zoom': {
            'DataType': 'String',
            'StringValue': args.zoom
        },
        'focus': {
            'DataType': 'String',
            'StringValue': args.focus
        },
        'bounds': {
            'DataType': 'String',
            'StringValue': args.bounds
        },
        'frame-rate': {
            'DataType': 'String',
            'StringValue': args.frame_rate
        },
        'frame-batch': {
            'DataType': 'String',
            'StringValue': args.frame_batch
        },
        'frame-total': {
            'DataType': 'String',
            'StringValue': args.frame_total
        },
        'time-out': {
            'DataType': 'String',
            'StringValue': args.time_out
        },
    },
)

print(response['MessageId'])