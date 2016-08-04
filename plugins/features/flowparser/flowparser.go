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
    "os/exec"
    "strings"
    "bufio"

    "github.com/streadway/amqp"
    "github.com/DanielArndt/flowtbag"
)

func failOnError(err error, msg string) {
    if err != nil {
        log.Fatalf("%s: %s", msg, err)
        panic(fmt.Sprintf("%s: %s", msg, err))
    }
}

func CheckError(err error, success_msg string, error_msg string) bool {
    if err != nil {
        fmt.Println(error_msg)
        return false
    } else {
        fmt.Println(success_msg)
        return true
    }
}

func Connect() {
    for {
        conn, err := amqp.Dial("amqp://guest:guest@rabbitmq:5672/")
        if CheckError(err, 
                    "connected to rabbitmq", 
                    "could not connect to rabbitmq, retrying...") {
            break
        }
    }

    for {
        ch, err := conn.Channel()
        if CheckError(err, 
                    "channel connected", 
                    "could not establish rabbitmq channel, retrying...") {
            break
        }
    }

    err = ch.ExchangeDeclare(
            "topic_poseidon_internal",
            "topic",
            true,
            false,
            false,
            false,
            nil,
    )
    failOnError(err, "failed to declare exchange, exiting")

    queue_name := "process_features_flowparser"
    _, err := ch.QueueDeclare(queue_name, true, true, false, false, nil)
    failOnError(err, "queue declaration failed, exiting")

    argc := len(os.Args)
    if argc > 2 {
        for i := 2; i < argc; i++ {
            err := ch.QueueBind(queue_name, os.Args[i], "topic_poseidon_internal", false, nil)
            failOnError(err, "queue bind failed, exiting")
        }
    } else {
        log.Fatalf("Usage: %s [file_name] [binding_key]...", os.Args[0])
        panic(fmt.Sprintf("Usage: %s [file_name] [binding_key]...", os.Args[0]))
    }

    fmt.Println(" [*] Waiting for logs. To exit press CTRL+C")

    return conn, ch
}

func sendLine(line string, ch Channel) {
    err = ch.Publish(
            "topic_poseidon_internal",
            "poseidon.flowparser",
            false, 
            false,
            amqp.Publishing{
                ContentType: "text/plain",
                Body:        []byte (line)
            })
    if err != nil {
        log.Println("failed to send message: %s", line)
    } else {
        fmt.Println(" [*] Sent %s", line)
    }

}

func main() {
    conn, ch := Connect()

    file_name := os.Args[1]
    output_file := file_name + ".out"
    ret, err := exec.Command("./flowtbag", file_name, ">", output_file).Run()
    failOnError(err, "failed to parse pcap")

    file, err := os.Open(output_file)
    failOnError(err, "failed to open file")
    defer file.Close()

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        sendLine(scanner.Text(), ch)
    }
    failOnError(scanner.Err(), "failed to read file")

    ch.Close()
    conn.Close()
}
