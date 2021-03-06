/*
 * Copyright 1999-2008 University of Chicago
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy
 * of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

package org.nimbustools.messaging.gt4_0.factory;

import org.nimbustools.api._repr._CreateRequest;
import org.nimbustools.api.repr.CannotTranslateException;
import org.nimbustools.messaging.gt4_0.generated.metadata.logistics.VirtualNetwork_Type;

public interface TranslateNet {

    public void translateNetworkingRelated(_CreateRequest req,
                                           VirtualNetwork_Type net)
         throws CannotTranslateException;
}
