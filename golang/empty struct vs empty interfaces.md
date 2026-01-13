# Empty struct vs Empty interface

https://stackoverflow.com/questions/22770114/any-difference-in-using-an-empty-interface-or-an-empty-struct-as-a-maps-value-i

The empty struct and empty interface, though syntactically similar, are actually opposites. 

* `An empty struct holds no data; `
* `an empty interface can hold any type of value. `

If I see a map[MyType]struct{}, I know immediately that no values will be stored, only keys. 

If I see a map[MyType]interface{}, my first impression will be that it is a heterogenous collection of values. Even if I see code storing nil in it, I won't know for sure that some other piece of code doesn't store something else in it.

In other words, using struct{} makes your code much more readable. It also saves a little memory, as described in the other answer, but that is just a fringe benefit of using the right tool for the job.