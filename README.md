# Cloud-Scalable-Fault-Tolerant-Mandelbrot
A cloud system which is both scalable and fault tolerant for generating Mandelbrot zooms.
Inspired by the job observer pattern it consists of a client, a controller EC2 instance and several worker EC2 instances controlled by an Autoscaling group.
The client schedules work and the controller distributes this work as batches of frames through the use of SQS queues, which are monitored by Cloudwatch alarms to guide the autoscaling.
As work is completed it is stored in an EFS network file system, in the event of a fault any incomplete work is rescheduled by the controller and once all work is complete the controller renders the frames into a video.

|Zoom ~ 1 x 10<sup>-15</sup>|
|---------------------------|
|![](worker/outputs/zoom.gif)|
