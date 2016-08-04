/*
 *   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 * 
 * Uses flowtbag package to parse pcap files for netflow info
 * and sends produced csv to analysis modules with rabbitmq.
 *
 * Created on August 3, 2016
 * @author: lanhamt
 */

package main

import (
    "fmt"
    "log"
    "os"
    "strings"

    "github.com/streadway/amqp"
    "github.com/DanielArndt/flowtbag"
)

func checkConnection(err error, success_msg string, error_msg string) bool {
    if err != nil {
        fmt.Println(error_msg)
        return false
    } else {
        fmt.Println(success_msg)
        return true
    }
}

func connect() {
    for {
        conn, err := amqp.Dial("amqp://guest:guest@rabbitmq:5672/")
        if checkConnection(err, 
                            "connected to rabbitmq", 
                            "could not connect to rabbitmq, retrying...") {
            break
        }
    }
    defer conn.Close()

    for {
        ch, err := conn.Channel()
        if checkConnection(err, 
                            "channel connected", 
                            "could not establish rabbitmq channel, retrying...") {
            break
        }
    }
    defer ch.Close()

    err = ch.ExchangeDeclare(
            "topic_poseidon_internal",
            "topic",
            true,
            false,
            false,
            false,
            nil,
    )
    failOnError(err, "failed to declare exchange, exiting...")
}

func main() {
    connect()
}
