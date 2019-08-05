# 关于Pixiv的动图获取过程

### 主要依赖的JSON请求地址

1. https://www.pixiv.net/ajax/illust/illust-id/ugoira_meta

### 用到的返回类型

 1. **originalSrc**

 2. **mime_type**

 3. **frames**

## 基于Python的动图合成过程
### 依赖:imageio
### 代码:

```python
import imageio
 
def create_gif(image_list, gif_name):
 
    frames = []
    for image_name in image_list:
        frames.append(imageio.imread(image_name))
    # Save them as frames into a gif 
    imageio.mimsave(gif_name, frames, 'GIF', duration = 0.1)
 
    return
 
def main():
    image_list = ['test_gif-0.png', 'test_gif-2.png', 'test_gif-4.png', 
                  'test_gif-6.png', 'test_gif-8.png', 'test_gif-10.png']
    gif_name = 'created_gif.gif'
    create_gif(image_list, gif_name)
    
if __name__ == "__main__":
    main()    
```

#### 结束