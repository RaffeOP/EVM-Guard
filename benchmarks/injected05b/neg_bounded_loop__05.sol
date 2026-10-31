pragma solidity 0.5.12;

contract Wallet1458 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 8) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 8; i++) {
            if (i < members.length) members[i].balance;
        }
    }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
