import hashlib
import json
import pika
import sys
import requests

from languages import c_lang_config, cpp_lang_config, java_lang_config, c_lang_spj_config, \
    c_lang_spj_compile, py2_lang_config, py3_lang_config


class JudgeServerClientError(Exception):
    pass


class JudgeServerClient(object):
    def __init__(self, token, server_base_url):
        self.token = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.server_base_url = server_base_url.rstrip("/")

    def _request(self, url, data=None):
        kwargs = {"headers": {"X-Judge-Server-Token": self.token,
                              "Content-Type": "application/json"}}
        if data:
            kwargs["data"] = json.dumps(data)
        try:
            return requests.post(url, **kwargs).json()
        except Exception as e:
            raise JudgeServerClientError(str(e))

    def ping(self):
        return self._request(self.server_base_url + "/ping")

    def judge(self, src, language_config, max_cpu_time, max_memory, test_case_id, spj_version=None, spj_config=None,
              spj_compile_config=None, spj_src=None, output=False):
        data = {"language_config": language_config,
                "src": src,
                "max_cpu_time": max_cpu_time,
                "max_memory": max_memory,
                "test_case_id": test_case_id,
                "spj_version": spj_version,
                "spj_config": spj_config,
                "spj_compile_config": spj_compile_config,
                "spj_src": spj_src,
                "output": output}
        return self._request(self.server_base_url + "/judge", data=data)

    def compile_spj(self, src, spj_version, spj_compile_config):
        data = {"src": src, "spj_version": spj_version,
                "spj_compile_config": spj_compile_config}
        return self._request(self.server_base_url + "/compile_spj", data=data)


def judge(problemID, lang, code, memoryLimit, timeLimit):
    lang_config = java_lang_config
    if lang == 'c':
        lang_config = c_lang_config
    elif lang == 'cpp':
        lang_config = cpp_lang_config
    elif lang == 'py2':
        lang_config = py2_lang_config
    elif lang == 'py3':
        lang_config = py3_lang_config
    return client.judge(
        src=code,
        language_config=lang_config,
        max_cpu_time=timeLimit,
        max_memory=memoryLimit,
        test_case_id=problemID,
        output=False
    )


def consume(ch, method, properties, body):
    data = json.loads(body.decode())
    # print(data)
    print('[CONSUME] Preparing for submission ' + data['submitID'] + '...')
    submitID = data['submitID']
    problemID = data['problemID']
    preJudge = requests.post('http://oj.ll-ap.cn:3000/judger/start',
                             json={'submitID': submitID, 'judger': 'HKReporter'})
    preJudgeData = None
    try:
        preJudgeData = preJudge.json()
    except Exception:
        preJudgeData = {
            'err': 'Cannot get problem status',
        }
    memoryLimit = 128 * 1024 * 1024
    timeLimit = 1000
    if preJudgeData['err'] == '':
        memoryLimit = preJudgeData['memoryLimit']
        timeLimit = preJudgeData['timeLimit']
        print('[JUDGE] Override limit settings: %d bytes of memory, %d ms of time.' % (memoryLimit, timeLimit))
    print('[JUDGE] Start')
    judge_data = judge(problemID, data['compiler'], data['code'], memoryLimit, timeLimit)
    # print(judge_data)
    if not judge_data['err'] is None:
        # print("ERRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR")
        print('[ERROR] ' + judge_data['data'])
        ret = {
            'judger': 'HKReporter',
            'score': 0,
            'status': 6,
            'peakMemory': 0,
            'runtime': 0,
            'err': judge_data['data'],
            'results': None,
            'hash': '19260817'
        }
    else:
        # print("SUCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
        _score = 0
        _status = 0
        _time = 0
        _memory = 0
        _avgscore = 100 / len(judge_data['data'])
        for item in judge_data['data']:
            _time = _time + item['cpu_time']
            _memory = max(_memory, item['memory'])
            if item['result'] == 0:
                _score = _score + _avgscore
            else:
                if _status == 0:
                    _status = item['result']

        ret = {
            'judger': 'HKReporter',
            'score': _score,
            'status': _status,
            'peakMemory': _memory,
            'runtime': _time,
            'err': judge_data['err'],
            'results': judge_data['data'],
            'hash': '19260817'
        }
        print('[JUDGE] Successfully judged submission ' + submitID)
        print('[MSG] With score of %d' % (_score))
    # print(ret)
    print('[INFO] Sending results...')
    requests.post('http://oj.ll-ap.cn:3000/judger/judge/%s' % (submitID), json=ret)
    channel.basic_ack(delivery_tag=method.delivery_tag)
    print('[INFO] Queue acked.')


if __name__ == "__main__":
    token = "apoj"
    client = JudgeServerClient(token=token, server_base_url="http://127.0.0.1:12358")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            '118.89.102.93',
            credentials=pika.credentials.PlainCredentials(
                username='apoj',
                password='t3dv95my'
            ), socket_timeout=5
        )
    )
    channel = connection.channel()
    channel.queue_declare(
        queue="apoj_submit_queue",
        durable=True
    )

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(consume, queue='apoj_submit_queue')
    print('[INFO] Successfully started consuming... Press Ctrl+C to exit.')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print('Keyboard Interrupted. Closing connection...')
        connection.close()