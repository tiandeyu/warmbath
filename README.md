warmbath是一款松下风暖浴霸的homeassistant插件，能够更好的让浴霸通过红外的方式接入homeassistant

Home Assistant Custom Component for Panasonic Bathroom Master, homeassistant infrared integration

---

下载custom_components下面所有文件到如下目录/config/custom_components/

download all files from custom_components to your ha machine folder /config/custom_components/
```
//文件目录结构如下
//the folder should be the same as below
/config/custom_components/warmbath/__init__.py
/config/custom_components/warmbath/fan.py
/config/custom_components/warmbath/manifest.json
```

在configuration.yaml配置
add config to configuration.yaml
```$xslt
fan:
  - platform: warmbath
    name: 'Bathroom Master'
    command_topic: "cmnd/bathroom/IRSend"
    payload_close: '0,3512,1744,444,xxx'
    payload_heat: '0,3486,1770,472,xxx'
    payload_ventilate: '0,3486,1772,xxx'
    payload_cool: '0,3540,1712,444,xxx'
    payload_dry: '0,3540,1714,474,xxx'
```
