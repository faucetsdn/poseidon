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
 * Test package for flowparser.
 *
 * Created on August 3, 2016
 * @author: lanhamt
 */
package main

import (
	"errors"
	"testing"
)

/*
 * Tests failOnError function which logs an error and panics
 * when a valid error is passed to it (ie a non-nil error).
 */
func TestFailOnError(t *testing.T) {
	failOnError(nil, "test should not fail")
}

/*
 * Tests CheckError function which returns true when there is
 * no error (ie err = nil), and returns false when there is
 * an error.
 */
func TestCheckError(t *testing.T) {
	// test no error case
	ret := CheckError(nil, "Should print this out 1", "BAD")
	if !ret {
		t.Error("Return should have been true due to error.")
	}

	// test error case
	ret = CheckError(errors.New("test error"), "BAD", "should print this out 2")
	if ret {
		t.Error("Return should have been false.")
	}
}

/*
 * Tests RabbitConnect function which returns a rabbit
 * connection and channel after successfully connecting
 * to rabbitmq.
 */
func TestRabbitConnect(t *testing.T) {
	// INTEGRATION TEST
	// conn, ch := RabbitConnect()
	// t.Error(conn)
	// t.Error(ch)
}

/*
 * Tests sendLine function which sends given line to
 * given rabbitmq channel.
 */
func TestSendLine(t *testing.T) {
	// INTEGRATION TEST
	// sendLine("csv line to send", nil)
}

func TestMain(t *testing.T) {
	// INTEGRATION TEST
	// main()
}
