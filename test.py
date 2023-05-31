import pydoi as pydoi
import requests
from urllib.parse import urlparse

ret = pydoi.get_url("10.1016/j.chempr.2020.04.016")
print(ret)
