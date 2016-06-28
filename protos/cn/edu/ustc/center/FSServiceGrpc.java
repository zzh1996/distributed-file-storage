package cn.edu.ustc.center;

import static io.grpc.stub.ClientCalls.asyncUnaryCall;
import static io.grpc.stub.ClientCalls.asyncServerStreamingCall;
import static io.grpc.stub.ClientCalls.asyncClientStreamingCall;
import static io.grpc.stub.ClientCalls.asyncBidiStreamingCall;
import static io.grpc.stub.ClientCalls.blockingUnaryCall;
import static io.grpc.stub.ClientCalls.blockingServerStreamingCall;
import static io.grpc.stub.ClientCalls.futureUnaryCall;
import static io.grpc.MethodDescriptor.generateFullMethodName;
import static io.grpc.stub.ServerCalls.asyncUnaryCall;
import static io.grpc.stub.ServerCalls.asyncServerStreamingCall;
import static io.grpc.stub.ServerCalls.asyncClientStreamingCall;
import static io.grpc.stub.ServerCalls.asyncBidiStreamingCall;
import static io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall;
import static io.grpc.stub.ServerCalls.asyncUnimplementedStreamingCall;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 0.15.0-SNAPSHOT)",
    comments = "Source: api.proto")
public class FSServiceGrpc {

  private FSServiceGrpc() {}

  public static final String SERVICE_NAME = "center.FSService";

  // Static method descriptors that strictly reflect the proto.
  @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/1901")
  public static final io.grpc.MethodDescriptor<cn.edu.ustc.center.ApiProtos.FS_Request,
      cn.edu.ustc.center.ApiProtos.FS_Response> METHOD_FSSERVE =
      io.grpc.MethodDescriptor.create(
          io.grpc.MethodDescriptor.MethodType.UNARY,
          generateFullMethodName(
              "center.FSService", "FSServe"),
          io.grpc.protobuf.ProtoUtils.marshaller(cn.edu.ustc.center.ApiProtos.FS_Request.getDefaultInstance()),
          io.grpc.protobuf.ProtoUtils.marshaller(cn.edu.ustc.center.ApiProtos.FS_Response.getDefaultInstance()));

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static FSServiceStub newStub(io.grpc.Channel channel) {
    return new FSServiceStub(channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static FSServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    return new FSServiceBlockingStub(channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary and streaming output calls on the service
   */
  public static FSServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    return new FSServiceFutureStub(channel);
  }

  /**
   */
  public static interface FSService {

    /**
     */
    public void fSServe(cn.edu.ustc.center.ApiProtos.FS_Request request,
        io.grpc.stub.StreamObserver<cn.edu.ustc.center.ApiProtos.FS_Response> responseObserver);
  }

  @io.grpc.ExperimentalApi("https://github.com/grpc/grpc-java/issues/1469")
  public static abstract class AbstractFSService implements FSService, io.grpc.BindableService {

    @java.lang.Override
    public void fSServe(cn.edu.ustc.center.ApiProtos.FS_Request request,
        io.grpc.stub.StreamObserver<cn.edu.ustc.center.ApiProtos.FS_Response> responseObserver) {
      asyncUnimplementedUnaryCall(METHOD_FSSERVE, responseObserver);
    }

    @java.lang.Override public io.grpc.ServerServiceDefinition bindService() {
      return FSServiceGrpc.bindService(this);
    }
  }

  /**
   */
  public static interface FSServiceBlockingClient {

    /**
     */
    public cn.edu.ustc.center.ApiProtos.FS_Response fSServe(cn.edu.ustc.center.ApiProtos.FS_Request request);
  }

  /**
   */
  public static interface FSServiceFutureClient {

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<cn.edu.ustc.center.ApiProtos.FS_Response> fSServe(
        cn.edu.ustc.center.ApiProtos.FS_Request request);
  }

  public static class FSServiceStub extends io.grpc.stub.AbstractStub<FSServiceStub>
      implements FSService {
    private FSServiceStub(io.grpc.Channel channel) {
      super(channel);
    }

    private FSServiceStub(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FSServiceStub build(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      return new FSServiceStub(channel, callOptions);
    }

    @java.lang.Override
    public void fSServe(cn.edu.ustc.center.ApiProtos.FS_Request request,
        io.grpc.stub.StreamObserver<cn.edu.ustc.center.ApiProtos.FS_Response> responseObserver) {
      asyncUnaryCall(
          getChannel().newCall(METHOD_FSSERVE, getCallOptions()), request, responseObserver);
    }
  }

  public static class FSServiceBlockingStub extends io.grpc.stub.AbstractStub<FSServiceBlockingStub>
      implements FSServiceBlockingClient {
    private FSServiceBlockingStub(io.grpc.Channel channel) {
      super(channel);
    }

    private FSServiceBlockingStub(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FSServiceBlockingStub build(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      return new FSServiceBlockingStub(channel, callOptions);
    }

    @java.lang.Override
    public cn.edu.ustc.center.ApiProtos.FS_Response fSServe(cn.edu.ustc.center.ApiProtos.FS_Request request) {
      return blockingUnaryCall(
          getChannel(), METHOD_FSSERVE, getCallOptions(), request);
    }
  }

  public static class FSServiceFutureStub extends io.grpc.stub.AbstractStub<FSServiceFutureStub>
      implements FSServiceFutureClient {
    private FSServiceFutureStub(io.grpc.Channel channel) {
      super(channel);
    }

    private FSServiceFutureStub(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FSServiceFutureStub build(io.grpc.Channel channel,
        io.grpc.CallOptions callOptions) {
      return new FSServiceFutureStub(channel, callOptions);
    }

    @java.lang.Override
    public com.google.common.util.concurrent.ListenableFuture<cn.edu.ustc.center.ApiProtos.FS_Response> fSServe(
        cn.edu.ustc.center.ApiProtos.FS_Request request) {
      return futureUnaryCall(
          getChannel().newCall(METHOD_FSSERVE, getCallOptions()), request);
    }
  }

  private static final int METHODID_FSSERVE = 0;

  private static class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final FSService serviceImpl;
    private final int methodId;

    public MethodHandlers(FSService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_FSSERVE:
          serviceImpl.fSServe((cn.edu.ustc.center.ApiProtos.FS_Request) request,
              (io.grpc.stub.StreamObserver<cn.edu.ustc.center.ApiProtos.FS_Response>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    return new io.grpc.ServiceDescriptor(SERVICE_NAME,
        METHOD_FSSERVE);
  }

  public static io.grpc.ServerServiceDefinition bindService(
      final FSService serviceImpl) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          METHOD_FSSERVE,
          asyncUnaryCall(
            new MethodHandlers<
              cn.edu.ustc.center.ApiProtos.FS_Request,
              cn.edu.ustc.center.ApiProtos.FS_Response>(
                serviceImpl, METHODID_FSSERVE)))
        .build();
  }
}
