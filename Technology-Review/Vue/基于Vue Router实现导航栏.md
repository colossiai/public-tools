## **https://zhuanlan.zhihu.com/p/596578131**

## 

## **一、嵌套路由**

本篇文章有一个躲不过的基础概念——Vue Router的嵌套路由。

详细概念请一定移步官网仔细阅读，这里只是做个概述，帮助曾经阅读过官网的同学唤起记忆。

我们在路由定义文件router.js中定义过路由数据：

const routes = \[{ path: '/user/:id', component: User }\]

我们在页面入口文件APP.vue中定义过路由入口：

\<router-view\>\</router-view\>

当我们在main.js中引入router插件，就会自动把routes中定义的路由信息拿到，然后根据我们定义的事件，把对应的组件渲染到router-view中。

这里的意思就是把User组件渲染到router-view的位置。

**<span class="mark">如果User组件中还存在router-view标签，就是路由嵌套，则会在User中的router-view位置渲染routes中定义的对应的children内容</span>**。如：

const routes = \[

{

path: '/user/:id',

component: User,

children: \[

{

*// 当 /user/:id/profile 匹配成功*

*// UserProfile 将被渲染到 User 的 \<router-view\> 内部*

path: 'profile',

component: UserProfile,

},

{

*// 当 /user/:id/posts 匹配成功*

*// UserPosts 将被渲染到 User 的 \<router-view\> 内部*

path: 'posts',

component: UserPosts,

},

\],

},

\]

如果User组件的内容如下：

const User = {

template: \`

\<div class="user"\>

\<h2\>User {{ \$route.params.id }}\</h2\>

\<router-view\>\</router-view\>

\</div\>

\`,

}

那么就会在User组件中的router-view渲染UserProfile和UserPosts。

以上就是路由嵌套的大体内容。User可以视为父组件，UserProfile和UserPosts则为子组件。
