import json
import os
import xml.etree.ElementTree as ET
import subprocess
from urllib.parse import urlparse, parse_qs, urlencode, unquote, urlunparse, urljoin
import re
import sys
from datetime import datetime, timedelta
import time
import urllib3
from zoneinfo import ZoneInfo
import shutil
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, ROUND_HALF_UP



"""
This file contains functions to help with video processing.
Here are a list of all the functions to be used:
    * Functions for time conversion:
        -   format_duration_sec_to_H_M_S(seconds) => Converts seconds to H:M:S
        -   format_duration_H_M_S_to_sec(string) => convert H_M_S to seconds
        -   convert_AEDT(date_string) => convert a epoch TS in AEDT
        -   convert_duration_to_hms => 
        -   convert_to_sydney_time(utc_timestamp)
        -   class DurationManipulator(duration1,duration2)
            -   DurationManipulator.parse_duration_H_M_S_to_sec(duration)
            -   DurationManipulator.format_duration_sec_to_H_M_S(seconds)
            -   DurationManipulator.subtract_durations(seconds)
            -   DurationManipulator.addition_durations(seconds)
            -   DurationManipulator.extract_hours_minutes_seconds(duration_str)
            -   DurationManipulator.add_duration_to_timestamp(timestamp_str, duration_str)
            
    * Common Function for handling path/download/folder etc..:
        -   delete_file(file)
        -   concatenate_files(input_files, output_file)
        -   qs_parser(url) => QS parser to extract all QS
        -   HTTP_download( url_input, headers_in, folder ) => Download File
        -   copy_file_to_s3(bucket_name,s3_client,file_name,s3_key)
        -   baseURL_from_url(url) => #Function to provide the baseURL (no filename)
        -   filename_from_url(url) => #Function to provide a filename from URL without QS
        -   check_value_is_present(list_to_test,value)
        -   get_file_size(url)

    * Class for video :
        -   class IFrame|BFrame|PFrame|GOP => to extract GOP
        -   class VideoAnalyzer (file)
            -   VideoAnalyzer.analyze
        -   class DashManifestAnalyzer (manifest_file)
            -   DashManifestAnalyzer.manifest_info()
            -   DashManifestAnalyzer.period_manifest()
            -   DashManifestAnalyzer.period_info(period)
            -   DashManifestAnalyzer.adaption_set_info(period)
            -   DashManifestAnalyzer.scte35_parser(period)
            -   DashManifestAnalyzer.avc_profile_and_level(codec)
            -   DashManifestAnalyzer.find_period_with_asset_representation()
            -   DashManifestAnalyzer.find_period_without_asset_representation()

"""

#Function to delete file
def delete_file(file):
    # Check if the file exists before attempting to remove it
    print(file)
    if os.path.exists(file):
        if os.path.isfile(file) or os.path.islink(file):
            os.remove(file)  # remove the file
        elif os.path.isdir(file):
            shutil.rmtree(file)  # remove dir and all contains

    else:
        print(f"The file {file} does not exist.")


#Function to concatenate all fmp4 in a single file
def concatenate_files(input_files, output_file):
    # Concatenate a List of files
    with open(output_file, 'wb') as output:
        for input_file in input_files:
            with open(input_file, 'rb') as f:
                output.write(f.read())
   
   
#Function to copy to S3
def copy_file_to_s3(bucket_name,s3_client,file_name,s3_key):
    #s3_key = f'folder/test.mpd'  # Adjust path as needed
    try:
        if 'mp4' in file_name:
            s3_client.upload_file(file_name, bucket_name, s3_key, ExtraArgs={'ContentType': 'video/mp4'})
        else:
            s3_client.upload_file(file_name, bucket_name, s3_key)
        return {
            'statusCode': 200,
            'body': f'File {file_name} uploaded successfully to {bucket_name}/{s3_key}.'
        }
    except Exception as e:
        print(f'Error uploading file: {e}')
        return {
            'statusCode': 500,
            'body': 'Failed to upload file.'
        }
   
#Function to download a HTTP url on Lambda
def HTTP_download( url_input, headers_in, folder ):
    """Function to download through HTTP GET. Retrieves download time and headers
    input:
    -url: any URL
    -headers_in: HTTP headers to put ({'key':'value'}) 
        #headers_in = {'User-Agent': 'videotools'}
    # headers_in = {'Pragma':'akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-extracted-values, akamai-x-get-nonces, akamai-x-get-ssl-client-session-id, akamai-x-get-true-cache-key, akamai-x-serial-no, akamai-x-get-request-id','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3239.132 Safari/537.36'}

    -file
    output:
    -json dict:
        {"TS": str(datetime.datetime.now()),
            "URL": url_input,
            "download_duration":dwn_time,
            "codeRetour":code,
            "nb_header": str(len(headers_out)),
            "IP_Edge":edgeIP,
            "file_size":
            "headers":{}
    }
    """
    try:
        #manifest_req=HTTP_download(manifest_url,headers_in,folder_name)
        http = urllib3.PoolManager()
        start_time = time.time()
        response = http.request('GET', url_input, headers=headers_in,preload_content=False)
        end_time = time.time()
        current_directory = '/tmp/'
        parsed_url = urlparse(url_input)
        query_params = parsed_url.query
        if query_params:
            parsed_query_params = parse_qs(query_params)
            # Check if there are query parameters
            if parsed_query_params:
                # Remove query parameters
                parsed_url = parsed_url._replace(query='')
                file_name = os.path.basename(urlunparse(parsed_url))
            else:
                file_name = os.path.basename(path)
        path = parsed_url.path
        today = datetime.today()
        current_time = today.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"{current_time}_{os.path.basename(path)}" 
        final_file= folder+file_name
        #final_file= os.path.join(current_directory,save_path)
        dwn_time = end_time-start_time
        code=str(response.status)
        print(code)
        
        # Convert headers dictionary to JSON
        response_headers = {k: v for k, v in response.headers.items()}
        
        
        content_type = response.headers.get('Content-Type', '')
        print(content_type)
        if final_file != "":
            if response.status == 200:
                if 'application/octet-stream' in content_type or \
               'image/' in content_type or \
               'video/' in content_type or 'binary/octet-stream' in content_type :
                    # Save binary data
                    print(content_type)
                    #final_file += '.bin'  # Default extension for binary files
                    with open(final_file, 'wb') as out:
                        shutil.copyfileobj(response, out)
                else:
                    #for text file
                    data = response.data.decode('utf-8')
                    with open(final_file, 'w') as file:
                        file.write(data)
        file_stats = os.stat(final_file)
        # Release the connection
        response.release_conn()
        dict ={
            "timestamp": str(today),
            "url": url_input,
            "download_duration":dwn_time,
            "code":code,
            #"ip_edge":edgeIP,
            "file_name":final_file,
            "file_size":file_stats.st_size / (1024 * 1024)
        }
        dict["Headers"]=response_headers
        return dict
    except:
        print ("Unexpected error:", sys.exc_info()[0])
        return {'error':sys.exc_info()[0], 'code':code, 'headers':response_headers}

#Function to convert sec to H:M:S
def format_duration_sec_to_H_M_S( seconds):
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    return f"{hours:03d}:{minutes:02d}:{seconds:.3f}"

#Function to provide the baseURL (no filename)
def baseURL_from_url(url):
    # provide the filename from a URL without QS
    parsed_url = urlparse(url)
    path = parsed_url.path
    # Remove the last segment (filename) from the path
    path_without_filename = '/'.join(path.split('/')[:-1])
    # Reconstruct the URL without the filename
    base_uri = urlunparse((parsed_url.scheme, parsed_url.netloc, path_without_filename, '', '', ''))+'/'
    return base_uri

#Function to provide a filename from URL without QS
def filename_from_url(url):
    # provide the filename from a URL without QS
    parsed_url = urlparse(url)
    filename_with_query = os.path.basename(parsed_url.path)  # This includes the query string
    filename_without_query = os.path.splitext(filename_with_query)[0]
    return filename_without_query

def check_value_is_present(list_to_test,value):
    if list_to_test.get(value) is not None:
        response=list_to_test[value]
    else:
        response=None
    return response
      
#Function to get the filesize of a URL
def get_file_size(url):
    http = urllib3.PoolManager()

    try:
        response = http.request('HEAD', url)
        # Check the status code for success
        if response.status != 200:
            return {
                "statusCode": response.status,
                "body": f"Failed to fetch the file. Status code: {response.status}"
            }
        # Extract the Content-Length header
        content_length = response.headers.get('Content-Length')
        
        if content_length is None:
            return {
                "statusCode": 404,
                "body": "Content-Length header is missing"
            }
        else:
            file_size = int(content_length)
            return {
                "statusCode": 200,
                "body": file_size
            }
        int(content_length)
    except urllib3.exceptions.HTTPError as e:
        return {
            "statusCode": 500,
            "body": f"Error making HEAD request: {str(e)}"
        }
    
#Function to parse all QS in a url
def qs_parser(url):
    # Parse the URL
    parsed_url = urlparse(url)
    # Get the query string parameters
    query_params = parse_qs(parsed_url.query)
    dict_qs={}
    for key, values in query_params.items():
        for value in values:
            #print(f"{key}: {value}")
            dict_qs[key]=value
    return dict_qs

#Function to convert sec to H:M:S
def format_duration_sec_to_H_M_S( seconds):
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    return f"{hours:03d}:{minutes:02d}:{seconds:.3f}"

#Function to convert a duration in sec to HH:MM:SS
def convert_duration_to_hms(duration):
    if duration is not None:
        duration=str(duration)
        # Function to convert PTXXXX.YYYS into AH:BMCS.D
        # Use regular expression to extract seconds
        match = re.match(r"(\d+\.\d+)", duration)
        if 'PT' in duration:
        #seconds_str = duration
            seconds_str = duration.split('PT')[1].split('S')[0]
        else:
            seconds_str = duration

        if duration.find('.') != -1:
            # Extract the substring after 'PT' and before '.'
            seconds=int(seconds_str.split('.')[0])
            milliseconds_str = int(seconds_str.split('.')[1])
            # Convert the milliseconds part to an integer
            ms_seconds = int(milliseconds_str)
            
        else:
            seconds=int(seconds_str)
            ms_seconds = 0
            
        if match:
            hours = seconds // 3600
            remaining_seconds = seconds % 3600
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            # Format the new string
            new_duration = f"{hours}H{minutes}M{seconds}.{ms_seconds}"
            return new_duration
        else:
            return None
    else:
        return None


##### VIDEO ANALYSIS ######
class BFrame(object):
    def __repr__(self, *args, **kwargs):
        return "B"
    
    def __str__(self, *args, **kwargs):
        return repr(self)

class PFrame(object):
    def __repr__(self, *args, **kwargs):
        return "P"

    def __str__(self, *args, **kwargs):
        return repr(self)

class IFrame(object):
    
    def __init__(self):
        self.key_frame = False

    def __repr__(self, *args, **kwargs):
        if self.key_frame:
            return "I"
        else:
            return "i"
        
    def __str__(self, *args, **kwargs):
        return repr(self)

class GOP(object):
    
    def __init__(self):
        self.closed = False
        self.frames = []
        
    def add_frame(self, frame):
        self.frames.append(frame)
        
        if isinstance(frame, IFrame) and frame.key_frame:
            self.closed = True
            
    def __repr__(self, *args, **kwargs):
        frames_repr = ''
        
        for frame in self.frames:
            frames_repr += str(frame)
        
        gtype = 'CLOSED' if self.closed else 'OPEN'
        
        return 'GOP: {frames} {count} {gtype}'.format(frames=frames_repr, 
                                                      count=len(self.frames), 
                                                      gtype=gtype)

class VideoAnalyzer:
    
    def __init__(self, video_file):
        self.video_file = video_file

    def analyze(self):
        ffprobe_command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_frames",
            self.video_file
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        #resul=subprocess.call(['ffprobe', '-i', self.video_file])
   
        ffprobe_output = json.loads(result.stdout)
        if ffprobe_output:
            
            # Extract video stream information
            video_streams = [stream for stream in ffprobe_output['streams'] if stream['codec_type'] == 'video']
            if video_streams:
                video_stream = video_streams[0]  # Assuming only one video stream

                video_frames = ffprobe_output["frames"]
                #GOP Structure
                gop_count = 0
                gop_structure = []
                gop = GOP()
                gop_structure.append(gop)
                for jframe in video_frames:
                    if jframe["media_type"] == "video":
                        
                        frame = None
                        
                        if jframe["pict_type"] == 'I':
                            if len(gop.frames):
                                # GOP open and new iframe. Time to close GOP
                                gop = GOP()
                                gop_structure.append(gop)
                            frame = IFrame()
                            if jframe["key_frame"] == 1:
                                frame.key_frame = True
                        elif jframe["pict_type"] == 'P':
                            frame = PFrame()
                        elif jframe["pict_type"] == 'B':
                            frame = BFrame()
                        
                        frame.json = jframe
                        gop.add_frame(frame)
                max_gop_size=max(len(sublist.frames) for sublist in gop_structure)
                
                pattern = r"GOP:\s+([A-Z]+)\s+(\d+)\s+(CLOSED|OPEN)"
    
            
                gop_structure_dict=[]
                for gop_value in gop_structure:
                    # Search the string with the regular expression
                    match = re.search(pattern, str(gop_value))
                    if match:
                        # Extract values
                        gop_struct={
                            "gop": match.group(1),
                            "size": int(match.group(2)),
                            "status": match.group(3)
                            
                        }
                        gop_structure_dict.append(gop_struct)

                        
                dict_video=video_stream
                dict_video['maxGopSize']=max_gop_size
                
            else:
                dict_video={}

            
            # Extract video/audio frames
            video_frames = []
            audio_frames = []
            video_frames_small=[]
            audio_frames_small=[]
            frames=ffprobe_output["frames"]

            for i in range(len(frames)-1):
                dict_obj={}
                if frames[i]["media_type"] == "video":
                    dict_obj = {
                        'frame_index': i,
                        'size_bytes': int(frames[i]['pkt_size']),
                        'duration_time': check_value_is_present(frames[i],'duration_time'),
                        'pkt_dts_time': check_value_is_present(frames[i],'pkt_dts_time'),
                        'pkt_pos': frames[i]['pkt_pos'],
                        'type': frames[i]['pict_type'],
                        'key_frame': check_value_is_present(frames[i],'key_frame')
                    }
                    video_frames_small.append(dict_obj) 
                    video_frames.append(frames[i])
                if frames[i]["media_type"] == "audio":
                    dict_obj = {
                        'frame_index': i,
                        'size_bytes': int(frames[i]['pkt_size']),
                        'duration_time': check_value_is_present(frames[i],'duration_time'),
                        'pkt_dts_time': check_value_is_present(frames[i],'pkt_dts_time')
                        #'pkt_pos': frames[i]['pkt_pos']
                    }
                    audio_frames_small.append(dict_obj) 
                    audio_frames.append(frames[i]) 

            # Extract audio stream information
            audio_streams = [stream for stream in ffprobe_output['streams'] if stream['codec_type'] == 'audio']
            if audio_streams:
                audio_video_tag='audio'
                audio_stream = audio_streams[0]  # Assuming only one audio stream
                dict_audio=audio_stream

            else:
                dict_audio={}
            
            if len(video_frames_small) == 0:
                gop_structure_dict=[]
            results={
               "video": dict_video,
               "videoFrames": video_frames_small,
               "audio": dict_audio,
               "audioFrames": audio_frames_small,
               "format":ffprobe_output['format'],
               "gopStructure": gop_structure_dict

            }

            return results
        else:
            print("ffprobe error - check is file is a media")

#Class to Analyze DashManifest
class DashManifestAnalyzer:
    def __init__(self, manifest_root):
        self.manifest_root = manifest_root

    def manifest_info(self):
        # Function to extract all MPD parameters
        avail_start_time=self.manifest_root.get("availabilityStartTime")
        publish_time=self.manifest_root.get("publishTime")
        min_buffer_time=self.manifest_root.get("minBufferTime").replace("PT", "").replace("S", "")
        try:
            presentation_delay=self.manifest_root.get("suggestedPresentationDelay").replace("PT", "").replace("S", "")
        except:
            presentation_delay=''
        try:
            min_update_period=self.manifest_root.get("minimumUpdatePeriod").replace("PT", "").replace("S", "")
        except:
            min_update_period=''
            
        time_shift_buffer=self.manifest_root.get("timeShiftBufferDepth")
        manifest_type=self.manifest_root.get("type")
        if self.manifest_root.find(".//{urn:mpeg:dash:schema:mpd:2011}BaseURL"):
            base_url = self.manifest_root.find(".//{urn:mpeg:dash:schema:mpd:2011}BaseURL").text
        else:
            base_url=None
        if self.manifest_root.find(".//{urn:mpeg:dash:schema:mpd:2011}Location"):
            location = self.manifest_root.find(".//{urn:mpeg:dash:schema:mpd:2011}Location").text
        else:
            location=None
                      
        # Find all Periods and AdaptationSets
        number_periods = len(self.manifest_root.findall('.//{urn:mpeg:dash:schema:mpd:2011}Period'))
        number_adaptation_sets = len(self.manifest_root.findall('.//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet')[0])

        return {
                "availStartTime": avail_start_time,
                "publishTime": publish_time,
                "minUpdatePeriod": min_update_period,
                "minBufferTime": min_buffer_time,
                "presentationDelay": presentation_delay,
                "timeShiftBuffer": self.convert_duration_to_hms(time_shift_buffer),
                "manifestType" :manifest_type,
                "numberPeriods" :number_periods,
                "numberAdaptationSets" : number_adaptation_sets,
                "baseUrl" : base_url,
                "location" : location
            }
    
    def period_manifest(self):
        # Function to parse the MPEG-DASH manifest XML to extract all periods 
        periods=self.manifest_root.findall('.//{urn:mpeg:dash:schema:mpd:2011}Period')
        return periods
    
    def period_info(self, period_arg):
        # Function to parse the MPEG-DASH manifest XML to extract all periods 
        period_id=period_arg.get("id")
        period_duration=period_arg.get("duration")
        period_start=period_arg.get("start")
        
        if period_duration:
            if not ('H' in period_duration or 'M' in period_duration or 'S' in period_duration):
                period_duration=self.convert_duration_to_hms(period_arg.get("duration"))
            else:
                period_duration=period_arg.get("duration").replace("PT", "").replace("S", "")

        #convert into H:M:S to be more human readable
        if period_start:
            if not ('H' in period_start or 'M' in period_start or 'S' in period_start):
                #for vod content there are PTXS
                period_start=self.convert_duration_to_hms(period_arg.get("start"))
            else:
                period_start=period_arg.get("start").replace("PT", "").replace("S", "")
        period_base_url=period_arg.find(".//{urn:mpeg:dash:schema:mpd:2011}BaseURL")
       
        #get the max duration for represenation
        max_duration_video=0
        max_duration_audio=0
        max_duration_sub=0

        for adaptation_set in period_arg.findall('.//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet'):
            adaptation_mime_type = adaptation_set.get('mimeType')
            if 'image' not in adaptation_mime_type:
                
                for representation in adaptation_set.findall('.//{urn:mpeg:dash:schema:mpd:2011}Representation'):
                    segment_template = representation.find('.//{urn:mpeg:dash:schema:mpd:2011}SegmentTemplate')
                    if segment_template.get("timescale") is not None:
                        timescale = int(segment_template.get("timescale"))
                    else:
                        segment_template_init = adaptation_set.find('.//{urn:mpeg:dash:schema:mpd:2011}SegmentTemplate')
                        timescale = int(segment_template_init.get("timescale"))
            
                    segment_timeline = segment_template.find("{urn:mpeg:dash:schema:mpd:2011}SegmentTimeline")
                    #Listing All fragments
                    if segment_timeline is not None:
                        total_duration = 0
                        namespace = {'mpd': 'urn:mpeg:dash:schema:mpd:2011'}
                        s_elements = segment_timeline.findall('mpd:S', namespace)
                        for s in s_elements:
                            duration = int(s.get("d"))
                            repeat = int(s.get("r", default="0"))
                            if repeat == 0:
                                total_duration += duration
                            else:
                                for _ in range(repeat+1):
                                    total_duration += duration
                        duration= total_duration/timescale
                        if adaptation_mime_type == 'video/mp4':
                            if duration > max_duration_video :
                                max_duration_video=duration
                        elif adaptation_mime_type == 'audio/mp4':
                            if duration > max_duration_audio :
                                max_duration_audio=duration
                        elif adaptation_mime_type == 'application/mp4':
                            if duration > max_duration_sub :
                                max_duration_sub=duration
            max_duration={
                "video": format_duration_sec_to_H_M_S(max_duration_video),
                "audio": format_duration_sec_to_H_M_S(max_duration_audio),
                "subtitle": format_duration_sec_to_H_M_S(max_duration_sub)
             }
            
        return {
                "periodId": period_id,
                "periodDuration": period_duration,
                "periodStart": period_start,
                "periodBaseUrl": period_base_url,
                "periodMaxDuration": max_duration
            }

    def convert_duration_to_hms(self, duration):
        if duration is not None:
            # Function to convert PTXXXX.YYYS into AH:BMCS.D
            # Use regular expression to extract seconds
            match = re.match(r"PT(\d+\.\d+)S", duration)
            seconds_str = duration.split('PT')[1].split('S')[0]

            if duration.find('.') != -1:
                # Extract the substring after 'PT' and before '.'
                seconds=int(seconds_str.split('.')[0])
                milliseconds_str = int(seconds_str.split('.')[1])
                # Convert the milliseconds part to an integer
                ms_seconds = int(milliseconds_str)
                
            else:
                seconds=int(seconds_str)
                ms_seconds = 0
               
            if match:
                hours = seconds // 3600
                remaining_seconds = seconds % 3600
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                # Format the new string
                new_duration = f"{hours}H{minutes}M{seconds}.{ms_seconds}"
                return new_duration
            else:
                return None
        else:
            return None
        
    def adaption_set_info(self,period):
        # Parse the MPEG-DASH manifest XML

        adaption_set_info=[]
        # Analysing the 1st period
        #if ad period, different attributes like framerate (at the Adaptation set level)
        namespaces = {'ns': 'urn:mpeg:dash:schema:mpd:2011', 'cenc': 'urn:mpeg:cenc:2013'}
        for adaptation_set in period.findall('.//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet'):
            # Extract adaptation set attributes
            adaptation_set_id = adaptation_set.get('id')
            adaptation_mime_type = adaptation_set.get('mimeType')
            adaptation_lang = adaptation_set.get('lang')
            
            label_element = adaptation_set.find(".//{urn:mpeg:dash:schema:mpd:2011}Label")
            if label_element is not None:
                adaptation_lang_label = label_element.text
            else:
                adaptation_lang_label='N/A'
            essential_property = adaptation_set.find('EssentialProperty')
            coding_dependency = adaptation_set.find('codingDependency')

            # Check if the <EssentialProperty> element is present
            if coding_dependency is not None:
                adaptation_mime_type = adaptation_set.get('mimeType')+'_TrickMode'

            # Iterate through representations within each adaptation set
            for representation in adaptation_set.findall('.//{urn:mpeg:dash:schema:mpd:2011}Representation'):

                # Find all Representation elements

                # Find all ContentProtection elements within each Representation
                drm_type=[]
                for content_protection in representation.findall('.//{urn:mpeg:dash:schema:mpd:2011}ContentProtection'):
                    scheme_id_uri = content_protection.get('schemeIdUri')
                    drm_type.append(content_protection.get('value'))
                    
                # Extract representation attributes
                representation_id = representation.get('id')
                if adaptation_mime_type == 'application/mp4':
                    representation_codecs = adaptation_set.get('codecs')
                    representation_samplingRate='N/A'
                else:
                    representation_codecs = representation.get('codecs')
                    representation_codecs_profile='N/A'
                    representation_codecs_level='N/A'
                    representation_frameRate='N/A'

                
                if representation_codecs:
                    representation_codecs_profile, representation_codecs_level = self.avc_profile_and_level(representation_codecs)
                else:
                    representation_codecs_profile='N/A'
                    representation_codecs_level='N/A'
                representation_bandwidth = representation.get('bandwidth')
                representation_height = representation.get('height')
                representation_width = representation.get('width')
                representation_frameRate = representation.get('frameRate')
                if representation_frameRate is None or not representation_frameRate:
                    representation_frameRate=adaptation_set.get('frameRate')
                representation_samplingRate = representation.get('audioSamplingRate')
                        #displaying the summary
                representation_attribute={
                    "adaptation_set_id": adaptation_set_id,
                    "content_protection": drm_type,
                    "adaptation_mime_type": adaptation_mime_type,
                    "adaptation_lang": adaptation_lang,
                    "adaptation_lang_label": adaptation_lang_label,
                    "representation_codecs": representation_codecs,
                    "representation_codecs_profile": representation_codecs_profile,
                    "representation_codecs_level" :representation_codecs_level,
                    "representation_bandwidth": representation_bandwidth,
                    "representation_width": representation_width,
                    "representation_height":representation_height,
                    "representation_frameRate": representation_frameRate,
                    "representation_samplingRate": representation_samplingRate
                }
                adaption_set_info.append(representation_attribute)
        return adaption_set_info
    
    def scte35_parser(self,period_arg):
        # Function to extract the Splice Info
        event = period_arg[0]
        timescale = event.get('timescale')
        if event.find('.//{urn:scte:scte35:2013:xml}SpliceInsert'):
            splice_insert = event.find('.//{urn:scte:scte35:2013:xml}SpliceInsert')
            scte35_event_id = splice_insert.get('spliceEventId')
            avail_num=splice_insert.get('availNum')
            avails_expected=splice_insert.get('availsExpected')
            out_of_networkIndicator=splice_insert.get('outOfNetworkIndicator')
            splice_event_cancelIndicator=splice_insert.get('spliceEventCancelIndicator')
            splice_immediate_flag=splice_insert.get('spliceImmediateFlag')
            scte35_unique_program_id = splice_insert.get('uniqueProgramId')
            if splice_insert.find('.//{urn:scte:scte35:2013:xml}BreakDuration') is not None:
                if splice_insert.find('.//{urn:scte:scte35:2013:xml}BreakDuration').get('duration') is not None:
                    duration_seconds = int(splice_insert.find('.//{urn:scte:scte35:2013:xml}BreakDuration').get('duration'))/int(timescale)
            else:
                duration_seconds=0
            hours = int(duration_seconds // 3600)
            duration_seconds %= 3600
            minutes = int(duration_seconds // 60)
            duration_seconds %= 60
            scte35_duration=f"{hours:03d}:{minutes:02d}:{duration_seconds:.3f}"
            scte35_segmentation_type_id=None
            scte35_type='SpliceInsert'
            

        elif event.find('.//{urn:scte:scte35:2013:xml}SegmentationDescriptor'):
            time_signal = event.find('.//{urn:scte:scte35:2013:xml}SegmentationDescriptor')
            scte35_segmentation_type_id = time_signal.get('segmentationTypeId')
            scte35_event_id = time_signal.get('segmentationEventId')
            segmentation_duration = time_signal.get('segmentationDuration')
            if segmentation_duration:
                duration_seconds = int(segmentation_duration)/int(timescale)
                hours = int(duration_seconds // 3600)
                duration_seconds %= 3600
                minutes = int(duration_seconds // 60)
                duration_seconds %= 60
                scte35_duration=f"{hours:03d}:{minutes:02d}:{duration_seconds:.3f}"
            else:
                scte35_duration=None
            scte35_unique_program_id=None
            scte35_type='TimeSignal'
        else:
            scte35_event_id=None
            scte35_unique_program_id=None
            scte35_duration=None
            scte35_segmentation_type_id=None
            scte35_type=None
            avail_num=None
            avails_expected=None
            out_of_networkIndicator=None
            splice_event_cancelIndicator=None
            splice_immediate_flag=None
        return {
                "scte35Type": scte35_type,
                "scte35AvailNum": avail_num,
                "scte35AvailsExpected": avails_expected,
                "scte35OutOfNetworkIndicator": out_of_networkIndicator,
                "spliceEventCancelIndicator": splice_event_cancelIndicator,
                "scte35SpliceImmediateFlag": splice_immediate_flag,               
                "scte35SpliceEventId": scte35_event_id,
                "scte35UniqueProgramId": scte35_unique_program_id,
                "scte35SegmentationTypeId":scte35_segmentation_type_id,
                "scte35Duration": scte35_duration,

            }

    def avc_profile_and_level(self, codec):
        # Mapping of profile_idc and level_idc values to corresponding profiles and levels
        profile_map = {
            '42': 'Baseline',
            '4D': 'Main',
            '4E': 'Extended',
            '64': 'High',
            '6E': 'Hi10P',
            '7A': 'Hi422P',
            # Add more profiles as needed
        }
        level_map = {
            '400A': '1',
            '400B': '1.1',
            '400C': '1.2',
            '400D': '1.3',
            '4014': '2',
            '4015': '2.1',
            '4016': '2.2',
            '401E': '3',
            '001F': '3.1',
            '401F': '3.1',
            '0020': '3.2',
            '4020': '3.2',
            '4028': '4',
            '4029': '4.1',
            '402A': '4.2',
            '0028': '4',
            '0029': '4.1',
            '002A': '4.2',

            '4032': '5',
            '4033': '5.1',
            '4034': '5.2',        
            # Add more levels as needed
        }
        if 'avc1' in codec:
            # Extract profile_idc and level_idc from codec string
            profile_idc = codec[5:7].upper()
            level_idc = codec[7:11].upper()
            
            # Convert hexadecimal values to profile and level
            profile = profile_map.get(profile_idc, 'Unknown')
            level = level_map.get(level_idc, 'Unknown')
        else:
            profile=None
            level=None
        
        return profile, level
    
    def find_period_with_asset_representation(self):
        # Parse the MPEG-DASH manifest XML
        periods_with_ads=[]
        for period in self.manifest_root.findall('.//{urn:mpeg:dash:schema:mpd:2011}Period'):
            # Check if the media name contains 'asset'
   
            # Find periods containing representation with 'asset' in their name
            for adaptation_set in period.findall('.//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet'):
                # Iterate through representations within each adaptation set
                for representation in adaptation_set.findall('.//{urn:mpeg:dash:schema:mpd:2011}Representation'):
                    segment_template = representation.find('.//{urn:mpeg:dash:schema:mpd:2011}SegmentTemplate')
                    media_attribute = segment_template.get('media')
                    # Check if this is an adbreak from EMT
                    if 'asset' in media_attribute:
                        periods_with_ads.append(period)
                        break
                break
        return periods_with_ads
    
    def find_period_without_asset_representation(self):
        # Parse the MPEG-DASH manifest XML
        periods_without_ads=[]
        for period in self.manifest_root.findall('.//{urn:mpeg:dash:schema:mpd:2011}Period'):
            # Check if the media name contains 'asset'
   
            # Find periods containing representation with 'asset' in their name
            for adaptation_set in period.findall('.//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet'):
                # Iterate through representations within each adaptation set
                for representation in adaptation_set.findall('.//{urn:mpeg:dash:schema:mpd:2011}Representation'):
                    segment_template = representation.find('.//{urn:mpeg:dash:schema:mpd:2011}SegmentTemplate')
                    media_attribute = segment_template.get('media')
                    # Check if this is an adbreak from EMT
                    if 'asset' not in media_attribute:
                        periods_without_ads.append(period)
                        break
                break
        return periods_without_ads

 
class DurationManipulator:
    def __init__(self, duration1, duration2):
        self.duration1 = duration1
        self.duration2 = duration2

    def parse_duration_H_M_S_to_sec(self, duration):
        if 'H' in duration:
            hours = int(duration.split('H')[0])
            remaining_part = duration.split('H')[1]
            if 'M' in remaining_part:
                minutes = int(remaining_part.split('M')[0])
                seconds = float(remaining_part.split('M')[1])
            else:
                minutes = 0
                seconds = float(remaining_part)
        else:
            hours = 0
            if 'M' in duration:
                minutes = int(duration.split('M')[0])
                seconds = duration.split('M')[1]
                seconds=float(seconds) if seconds else 0.0
            else:
                minutes = 0
                seconds = float(duration)

        return hours * 3600 + minutes * 60 + seconds

    def format_duration_sec_to_H_M_S(self, seconds):
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds %= 60
        return f"{hours:03d}:{minutes:02d}:{seconds:.3f}"

    def subtract_durations(self):
        duration1_seconds = self.parse_duration_H_M_S_to_sec(self.duration1)
        duration2_seconds = self.parse_duration_H_M_S_to_sec(self.duration2)
        result_seconds = duration1_seconds - duration2_seconds
        return self.format_duration_sec_to_H_M_S(result_seconds)
    
    def addition_durations(self):
        duration1_seconds = self.parse_duration_H_M_S_to_sec(self.duration1)
        duration2_seconds = self.parse_duration_H_M_S_to_sec(self.duration2)
        result_seconds = duration1_seconds + duration2_seconds
        return self.format_duration_sec_to_H_M_S(result_seconds)

    def extract_hours_minutes_seconds(self, duration_str):
        # Split the duration string by 'H', 'M', and 'S' to extract hours, minutes, and seconds
        if 'H' in duration_str:
            hours = int(duration_str.split('H')[0])
            remaining_part = duration_str.split('H')[1]
            if 'M' in remaining_part:
                minutes = int(remaining_part.split('M')[0])
                seconds = float(remaining_part.split('M')[1])
            else:
                minutes = 0
                seconds = float(remaining_part)
        else:
            hours = 0
            if 'M' in duration_str:
                minutes = int(duration_str.split('M')[0])
                seconds = float(duration_str.split('M')[1])
            else:
                minutes = 0
                seconds = float(duration_str)

        

        return hours, minutes, seconds

    def add_duration_to_timestamp(self,timestamp_str, duration_str):
        # Parse the timestamp string to datetime object
        try:
            # Try parsing with milliseconds
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            #timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            # Fall back to parsing without milliseconds
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
        
        # Extract hours, minutes, and seconds from the duration string
        hours, minutes, seconds = self.extract_hours_minutes_seconds(duration_str)
        # Create a timedelta object for the duration
        duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        # Add the duration to the timestamp
        new_timestamp = timestamp + duration
        return new_timestamp    