import requests, time, json
from key_config import API_KEY_ASSEMBLYAI, API_KEY_LISTENNOTES
from datetime import datetime
import pprint

# listen notes is a dB of podcasts
# upload to assemblyai

transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
assemblyai_headers = {'authorization': API_KEY_ASSEMBLYAI}  # used for authentication

listennotes_episode_endpoint = "https://listen-api.listennotes.com/api/v2/episodes"
listennotes_headers = {'X-ListenAPI-Key': API_KEY_LISTENNOTES}

def get_episode_audio_url(episode_id):
    url = listennotes_episode_endpoint + '/' + episode_id
    response = requests.request('GET', url, headers = listennotes_headers)
    data = response.json()
    pprint.print(data)

    episode_title = data['title']
    thumbnail = data['thumbnail']
    podcast_title = data['podcast']['title']
    audio_url = data['audio']

    return audio_url, thumbnail, podcast_title, episode_title

# transcribe
def transcribe(audio_url, auto_chapters):
    transcript_request = { 
        'audio_url': audio_url,  # url response from assemblyai in the upload
        'auto_chapters': auto_chapters
    }
    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=assemblyai_headers)  # 
    #print(transcript_response.json())
    job_id = transcript_response.json()['id']
    return job_id

#audio_url = upload(filename)
# transcript_id = transcribe(audio_url)
#print(transcript_id)


# poll to see when transcription done
# Send get request instead of post. Use polling endpoint. Not sending any data so just need endpoint and headers. Just asking for status.
# When sending data to API use post request. If only getting information/status use the get request.
def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    polling_response = requests.get(polling_endpoint, headers=assemblyai_headers)
    #print(polling_response.json())
    return polling_response.json()

def get_transcription_result_url(audio_url, auto_chapters):
    transcript_id = transcribe(audio_url, auto_chapters)
    while True:
        data = poll(transcript_id)  # seen in response as polling_response.json()['status']
        if data['status'] == 'completed':  
            return data, None
        elif data['status'] == 'error':
            return data, data["error"]
        print('Waiting 60 seconds')
        time.sleep(60)

# Save transcription. Notice went from from 'filename' to 'title' for file naming
def save_transcript(episode_id):
    audio_url, thumbnail, podcast_title, episode_title = get_episode_audio_url(episode_id)
    data, error = get_transcription_result_url(audio_url, auto_chapters=True)
    if data:
        filename = episode_id + '.txt'
        with open(filename, 'w') as f:
            f.write(data['text'])

        filename = episode_id + '_chapters.json'
        with open(filename, 'w') as f:
            chapters = data['chapters']

            data = {'chapters': chapters}
            data['audio_url']=audio_url
            data['thumbnail']=thumbnail
            data['podcast_title']=podcast_title
            data['episode_title']=episode_title
            # for key, value in kwargs.items():
            #     data[key] = value

            json.dump(data, f, indent=4)
            print('Transcript saved')
            return True
    elif error:
        print("Error!!!", error)
        return False