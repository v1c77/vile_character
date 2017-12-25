---
title: go 入门（day 1）
date: 2017-03-10 16:20:49
categories:
- develop
tags:
- go
---

> Hello world!

<!--more-->
# go tour 部分习题

> ## slice

```go
package main

import (
	"golang.org/x/tour/pic"
	"math"
)


func Pic(dx, dy int) [][]uint8 {
	myret := make([][]uint8, dy)
	for i := 0; i < dy ; i++{
		myret[i] = make([]uint8, dx)
		for j := 0; j < dx ; j++ {
			myret[i][j] = uint8(float64(j) * math.Log(float64(i)))
		}

	}
	return myret
}


func main() {
	pic.Show(Pic)
}

```

> ## maps

```go
package main

import (
	"golang.org/x/tour/wc"
	"strings"
)

func WordCount(s string) map[string]int {

	words := strings.Fields(s)
	myret := make(map[string]int)
	for _, word := range words{
		myret[word] += 1
	}
	return myret
}

func main() {
	wc.Test(WordCount)
}
```

> ## exercise-fibonacci-closure.go

```go
package main

import "fmt"

// fibonacci is a function that returns
// a function that returns an int.
func fibonacci() func() int {
	start, next := 0, 1

	return func() int {
		ret := start
		start, next = next, start+next
		return ret
	}

}

func main() {
	f := fibonacci()
	for i := 0; i < 10; i++ {
		fmt.Println(f())
	}
}

```


-------------
