pragma solidity 0.8.20;

contract Escrow3501 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }
}
